.. image:: https://readthedocs.org/projects/multilevel-py/badge/?version=latest

multilevel_py
=============

*Multilevel_py* is a library that simplifies the construction of classification hierarchies over more than two levels.
The framework depends on python3 only and implements a "deep instantiation" mechanism using pythons metaprogramming
facilities. In academia the addressed topic is also discussed under the term "Multilevel (Meta-) Modelling". Since
there is no corresponding framework in the python community until this point, multilevel_py was built to fill this gap.

Installing
----------

Install and update using `pip`_:

.. code-block:: text

    pip install multilevel_py


A Simple Example
----------------
 
 The following code constructs a classification structure that spans three levels.

.. code-block:: python

    from multilevel_py.constraints import is_int_constraint, is_str_constraint
    from multilevel_py.core import create_clabject_prop, Clabject
    
    Breed = Clabject(name="Breed")
    yearReg = create_clabject_prop(n="yearReg", t=1, f=0, i_f=True, c=[is_int_constraint])
    age = create_clabject_prop(n="age", t=2, f=0, i_f=True, c=[is_int_constraint])
    Breed.define_props([yearReg, age])
    
    Collie = Breed(name="Collie", init_props={"yearReg": 1888})
    lassie = Collie(name="Lassie", init_props={"age": 7}, declare_as_instance=True)

Visualisation
-------------
Using the viz module (requires installation of `pygraphviz`_) the following graph can be rendered for the previous
example:

.. image:: https://github.com/dataPuzzler/multilevel_py/blob/master/docs/images/collie_chain_initial_example.png
    :width: 400
    :alt: Visulisation of the collie example



Links
-----
* Github Repository: https://github.com/dataPuzzler/multilevel_py
* Documentation: https://multilevel-py.readthedocs.io/en/latest/
* Releases: https://pypi.org/project/multilevel-py/#description

.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _pygraphviz: https://pygraphviz.github.io/documentation/latest/index.html
