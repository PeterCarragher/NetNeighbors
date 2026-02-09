from setuptools import setup, find_packages

setup(
    name='dash_force_graph',
    version='0.1.0',
    description='Dash component wrapping force-graph for high-performance graph visualization',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'dash>=2.0.0',
    ],
    package_data={
        'dash_force_graph': ['bundle.js'],
    },
)
