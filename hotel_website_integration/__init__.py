from . import controllers
from . import models

def post_init_hook(cr, registry):
    from .migrations.post_init_hook import post_init_hook as migrate_rooms
    migrate_rooms(cr, registry)