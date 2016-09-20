import os, glob

import django.db.transaction

from gips.utils import verbose_out


"""API for the DB inventory for GIPS.

Provides a clean interface layer for GIPS callers to do CRUD ops on the
inventory DB, mostly by interfacing with dbinv.models.  Due to Django
bootstrapping weirdness, some imports have to be done in each function's
body.
"""


def rectify(asset_class):
    """Rectify the inventory database against the filesystem archive.

    For the current driver, go through each asset in the filesystem
    and ensure it has an entry in the inventory database.  Also
    remove any database entries that match no archived files.
    """
    # can't load this at module compile time because django initialization is crazytown
    from . import models
    # this assumes this directory layout:  /path-to-repo/tiles/*/*/
    path_glob = os.path.join(asset_class.Repository.data_path(), '*', '*')

    for (ak, av) in asset_class._assets.items():
        file_iter = glob.iglob(os.path.join(path_glob, av['pattern']))
        touched_rows = [] # for removing entries that don't match the filesystem
        with django.db.transaction.atomic():
            add_cnt = 0
            update_cnt = 0
            for f_name in file_iter:
                a = asset_class(f_name)
                (asset, created) = models.Asset.objects.update_or_create(
                    asset=a.asset,
                    sensor=a.sensor,
                    tile=a.tile,
                    date=a.date,
                    name=f_name,
                    driver=asset_class.Repository.name.lower(),
                )
                asset.save()
                touched_rows.append(asset.pk)
                if created:
                    add_cnt += 1
                    verbose_out("Asset added to database:  " + f_name, 4)
                else:
                    update_cnt += 1
                    verbose_out("Asset found in database:  " + f_name, 4)
            # Remove things from DB that are NOT in FS:
            deletia = models.Asset.objects.filter(asset=ak).exclude(pk__in=touched_rows)
            del_cnt = deletia.count()
            if del_cnt > 0:
                deletia.delete()
            msg = "{} complete, inventory records changed:  {} added, {} updated, {} deleted"
            print msg.format(ak, add_cnt, update_cnt, del_cnt) # no -v for this important data


def list_tiles(driver):
    """List tiles for which there are extant asset files for the given driver."""
    from .models import Asset
    return Asset.objects.filter(driver=driver).values_list('tile', flat=True).distinct()


def add_asset(**values):
    """(very) thin convenience method that wraps models.Asset().save().

    Arguments:  asset, sensor, tile, date, name, driver; passed directly
    into models.Asset().
    """
    from .models import Asset
    a = Asset(**values)
    a.save()
    return a # in case the user needs it


def add_product(**values):
    """(very) thin convenience method that wraps models.Product().save().

    Arguments:  driver, product, sensor, tile, date, name; passed
    directly into models.Product().
    """
    from .models import Product
    p = Product(**values)
    p.save()
    return p # in case the user needs it


def update_or_add_asset(driver, asset, tile, date, sensor, name):
    """Update an existing model or create it if it's not found.

    Convenience method that wraps update_or_create.  The first four
    arguments are used to make a unique key to search for a matching model.
    """
    from . import models
    query_vals = {
        'driver': driver,
        'asset':  asset,
        'tile':   tile,
        'date':   date,
    }
    update_vals = {'sensor': sensor, 'name': name}
    (asset, created) = models.Asset.objects.update_or_create(defaults=update_vals, **query_vals)
    return asset # in case the user needs it


def product_search(**criteria):
    """Perform a search for asset models matching the given criteria.

    Under the hood just calls models.Asset.objects.filter(**criteria);
    see Django ORM docs for more details.
    """
    from gips.inventory.dbinv import models
    return models.Product.objects.filter(**criteria)


def asset_search(**criteria):
    """Perform a search for asset models matching the given criteria.

    Under the hood just calls models.Asset.objects.filter(**criteria);
    see Django ORM docs for more details.
    """
    from gips.inventory.dbinv import models
    return models.Asset.objects.filter(**criteria)