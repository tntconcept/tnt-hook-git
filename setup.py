import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="TNTGitHook",
    version="0.2.2",
    author="Daniel Otero",
    author_email="dotero@autentia.com",
    description="Utility to auto imputate activities in TNT",
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
    install_requires=['requests', 'keyring'],
    scripts=["bin/TNTGitHook"],
    package_data={
        "TNTGitHook": ["misc/pre-push.sh"]
    }
)
