from os import listdir

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'SpaceBusGame'
copyright = '2020, Paul de Fromont'
author = 'Paul de Fromont'

# creating custom file
with open('scenario_list.rst', 'w') as file:
    file.write('.. scenario_list_')
    for scenario in [f for f in listdir('../../data/scenarios') if f.endswith('.xml')]:
        name = scenario.strip().replace('.xml', '').replace('_', ' ')
        file.write('\n\n{0}\n{1}\n\n.. literalinclude:: ../../data/scenarios/{2}\n\t:language: xml'
                   .format(name, '#' * len(name), scenario))

# The full version, including alpha/beta/rc tags
release = '2.0.0'

# -- General configuration ---------------------------------------------------

# remove folder's names
add_module_names = False

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.viewcode',
              'sphinx.ext.autosummary',
              'sphinx.ext.napoleon',
              'sphinx.ext.coverage',
              'sphinx.ext.graphviz',
              'sphinx.ext.doctest',
              'sphinx.ext.inheritance_diagram',
              'sphinx.ext.intersphinx',
              'sphinx.ext.todo',
              'sphinx.ext.coverage',
              'sphinx.ext.ifconfig',
              'sphinx.ext.mathjax'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# include to do boxes
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
html_theme_options = {
    'canonical_url': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_logo = '_static/logo.png'
html_favicon = '_static/logo.ico'

# Libraries that should not be parsed
autodoc_mock_imports = ['pyspark',
                        'crossfit_package',
                        'findspark',
                        'matplotlib',
                        'numpy',
                        'xgboost',
                        'pandas',
                        'django',
                        'sqlalchemy',
                        'scipy',
                        'sklearn',
                        'statsmodels',
                        'tqdm'
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
