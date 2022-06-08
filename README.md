# アプリケーションを超えてデータマイグレーション

## 状況説明
‐ 複数モデルを定義したアプリケーションがあります。
‐ そのうち１つのモデルをリファクタリングなどで独立させたい。具体的にはapp1.modelsモジュールからapp2.modelsモジュールへの移動を検討します。空虚なモデルですがあしからず...

```python
from django.db import models


class Model1(models.Model):
    attr1 = models.CharField(max_length=100)
    attr2 = models.CharField(max_length=100)

# このモデルを独立させる
class Model2(models.Model):
    attr1 = models.CharField(max_length=100)
    attr2 = models.CharField(max_length=100)
```

- しかし、運用中であるためデータも移動を行います。
```
$ python manage.py shell

>>> Model2.objects.all()
<QuerySet [<Model2: Model2 object (1)>, <Model2: Model2 object (2)>]>
```

- このような場合は、データマイグレーションとスキーママイグレーションのファイルを分けるのがベストプラクティスみたいです。https://selfs-ryo.com/detail/django_migrations_2
- DDL(Data Definition Language)、これは『CREATE DATABASE』コマンドや『CREATE TABLE』のようなDBの操作のことですが、DDLをトランザクション内で行うかどうかはデータベース製品によって異なるようです。
- Djangoはマイグレーションで失敗した場合、自動でロールバックしようとしますが前述のようにトランザクション内で行わないデータベース製品の場合エラーになってしまいます。
- スキーママイグレーションファイルとデータマイグレーションファイルを分割することでファイル単位の実行となるため、うまくマイグレートとロールバックを機能させることができます。

## 実装
- まずはアプリケーションをつくります。
```
$ python manage.py startapp app2
```
- モデルを定義します。
```python
# app2/models.py

from django.db import models


class Model2(models.Model):
    attr1 = models.CharField(max_length=100)
    attr2 = models.CharField(max_length=100)
```

‐ INSTALLED_APPSにアプリを追加したら新しいモデルのスキーママイグレーションファイルを生成します。
```
$ python manage.py makemigrations app2
```
- 続けてデータマイグレーション用のファイルを生成します。
```
$ python manage.py makemigrations --empty app1
```
```python
# app1/migrations/0002_auto_XXXXXXXXXXX.py
from django.db import migrations


def migrate_model2_data(apps, schema_editor):
    """
    model2データをマイグレート
    app1.modelsモジュールからapp2.modelsモジュールのモデルへデータ移動
    """
    old_model2_model = apps.get_model('app1', 'Model2')
    new_model2_model = apps.get_model('app2', 'Model2')
    for old_model2 in old_model2_model.objects.all():
        new_model2_model.objects.create(
            attr1=old_model2.attr1,
            attr2=old_model2.attr2
        )


def rollback_model2_data(apps, schema_editor):
    """
    model2データをロールバック
    app2.modelsモジュールからapp1.modelsモジュールのモデルへデータ移動
    """
    old_model2_model = apps.get_model('app1', 'Model2')
    new_model2_model = apps.get_model('app2', 'Model2')
    for new_model2 in new_model2_model.objects.all():
        old_model2_model.objects.create(
            attr1=new_model2.attr1,
            attr2=new_model2.attr2
        )


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0001_initial'),
        # app2のスキーママイグレーションより後に実行する
        ('app2', '0001_initial')
    ]

    operations = [
        migrations.RunPython(
            code=migrate_model2_data,
            reverse_code=rollback_model2_data
        )
    ]
```
- ポイントは実行する順番です。dependenciesに新しいモデルを作成するスキーママイグレーションへの依存を登録します。

- 最後にapp1のmodel2を削除(コメントアウト)してスキーママイグレーションファイルを作成します。
- これで2つのスキーママイグレーションファイルと1つのデータマイグレーションファイルを生成させました。
```
- app2 - 0001_initial.py # スキーママイグレーションその１

- app1 - 0001_initial.py
         0002_auto_XXXXXXXX_XXXX.py # データマイグレーション
         0003_delete_model2.py # スキーママイグレーションその２
```
- app2.modelsのモデルを作らせてから、データマイグレーションを行い、最後にapp1.modelsのモデルを削除するという順番で実行されます。
- 早速マイグレーション、ロールバックを試してみます。

```
# マイグレーションを実行
$ python manage.py migrate
...

$ python manage.py shell
>>> from app2.models import Model2
>>> Model2.objects.all()
<QuerySet [<Model2: Model2 object (1)>, <Model2: Model2 object (2)>]>

うん。OK!

# ロールバックを実行
$ python manage.py migrate app1 0001
Operations to perform:
  Target specific migration: 0001_initial, from app1
Running migrations:
  Rendering model states... DONE
  Unapplying app1.0003_delete_model2... OK
  Unapplying app1.0002_auto_20220607_1749... OK

# コメントアウトを外してapp1.models.Model2を有効化して
$ python manage.py shell
>>> from app1.models import Model2
>>> Model2.objects.all()
<QuerySet [<Model2: Model2 object (1)>, <Model2: Model2 object (2)>]>

ちゃんと戻ってる！
```
- 0003_delete_model2.pyのスキーママイグレーションの実行で一度、テーブルを削除しているにもかかわらずロールバックを書いたことによってデータの値を元に戻すことができるようになりました。
