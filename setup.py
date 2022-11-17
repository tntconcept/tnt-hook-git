import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="TNTGitHook",
    version="0.6.1",
    author="Autentia",
    author_email="info@autentia.com",
    description="Utility to auto impute activities in TNT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/autentia/internal/TNTGitHook.git",
    packages=setuptools.find_packages(),
    license='Unlicense',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['requests==2.26.0', 'keyring==23.11.0'],
    scripts=["bin/TNTGitHook"],
    package_data={
        "TNTGitHook": ["misc/tnt_git_hook.sh"]
    }
)
