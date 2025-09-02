# -*- coding: utf-8 -*-

from . import models
from . import wizard




def set_discount_fix_decimal(env):
    discount_fix = env.ref('account_fix_discount.decimal_discount_fix', False)
    if discount_fix:
        discount_fix.digits = 10

def _post_init(env):
    set_discount_fix_decimal(env)