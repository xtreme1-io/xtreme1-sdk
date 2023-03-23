import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xtreme1-sdk",
    version="0.6",
    author="Basic AI",
    author_email="nico@basic.ai",
    description="xtreme1 sdk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xtreme1-io/xtreme1-sdk.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'rich',
        'requests',
        'nanoid'
    ],
    entry_points={
        'console_scripts': ['xtreme1_ctl=xtreme1.console_scripts:main'],
    },
    python_requires='>=3.9',
)
