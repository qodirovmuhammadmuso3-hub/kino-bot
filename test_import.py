try:
    from aiogram.filters import CommandObject
    print("CommandObject imported from aiogram.filters")
except ImportError:
    print("Cannot import CommandObject from aiogram.filters")

try:
    from aiogram.filters.command import CommandObject
    print("CommandObject imported from aiogram.filters.command")
except ImportError:
    print("Cannot import CommandObject from aiogram.filters.command")
