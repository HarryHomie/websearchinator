from setuptools import setup

APP = ['web_searchinator.py']
DATA_FILES = [('', ['icon.png'])]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'Web Search-inator',
        'CFBundleDisplayName': 'Web Search-inator',
        'CFBundleGetInfoString': "Auto Search Tool",
        'CFBundleIdentifier': "com.websearchinator.app",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "© 2025",
        'NSHighResolutionCapable': True,
    },
    'packages': ['tkinter', 'PIL'],
    'includes': ['PIL.Image', 'PIL.ImageTk'],
}

setup(
    name='Web Search-inator',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=['Pillow'],
)