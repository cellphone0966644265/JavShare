# /core/config_manager.py
import configparser
import os

CONFIG_FILE = 'config.ini'
ACCOUNTS_FILE = 'accounts.ini'

def get_category_config(category_name):
    """Đọc cấu hình cho một danh mục từ config.ini."""
    if not os.path.exists(CONFIG_FILE):
        return None
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if category_name in config:
        return dict(config[category_name])
    return None

def get_account_creds(service_name):
    """Đọc thông tin tài khoản cho một dịch vụ từ accounts.ini."""
    if not os.path.exists(ACCOUNTS_FILE):
        return None
    config = configparser.ConfigParser()
    config.read(ACCOUNTS_FILE)
    if service_name in config:
        return dict(config[service_name])
    return None
