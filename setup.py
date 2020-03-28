from setuptools import setup


setup(name = 'auto-ru-tracker',
    version = '1.0',
    url = 'https://github.com/defunator/auto-ru-tracker',
    author = 'defunator',
    author_email = 'semyonli21@gmail.com',
    description = 'A telegram bot that tracks auto.ru ads.',
    packages = ['src'],
    scripts = ['track'],
    install_requires = ['beautifulsoup4', 'requests', 'pandas', 'lxml']
)