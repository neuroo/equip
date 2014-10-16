Installation
============

equip does not have any dependencies and is available on PyPi::

  $ pip install equip

You can also install equip using the ``setup.py``::

  $ git clone https://github.com/neuroo/equip.git
  $ cd equip
  $ python setup.py develop


Current Limitations
-------------------
The current version of equip only supports Python 2.7. It has not been tested on
any other versions. Actually, if you try to run it on a different version, you'll
get an exception complaining about the mismatching version.


The more practical way to use equip is however to leverage :ref:`virtualenv`.

.. _virtualenv:

virtualenv
----------
During testing and to instrument different part of the program, it is useful to deploy
the program under a virtual env. Here are the few steps to create a virtualenv::

  $ sudo pip install virtualenv
  $ mkdir project
  $ cd project
  $ virtualenv test-env
  $ . test-env/bin/activate

Under this virtual environment, you can install equip the same way::

  $ pip install equip

