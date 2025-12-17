Contributing
============

Thank you for your interest in contributing to the Cloudflare SaaS Platform library!

Getting Started
---------------

Development Setup
^^^^^^^^^^^^^^^^^

1. Fork and clone the repository:

.. code-block:: bash

   git clone https://github.com/yourusername/cloudflare-saas.git
   cd cloudflare-saas

2. Install development dependencies:

.. code-block:: bash

   pip install -e ".[dev,web]"

3. Set up pre-commit hooks:

.. code-block:: bash

   pre-commit install

4. Create a .env file for testing:

.. code-block:: bash

   cp .env.example .env
   # Edit .env with your test credentials

Running Tests
^^^^^^^^^^^^^

.. code-block:: bash

   # Run all tests
   make test

   # Run with coverage
   make test-cov

   # Run specific test file
   pytest tests/test_platform.py -v

Code Quality
------------

Linting
^^^^^^^

.. code-block:: bash

   # Check code style
   make lint

   # Auto-format code
   make format

We use:

- **Black**: Code formatting
- **Ruff**: Fast linting
- **MyPy**: Type checking

Type Hints
^^^^^^^^^^

All functions should include type hints:

.. code-block:: python

   from typing import Optional, List

   async def create_tenant(
       name: str,
       slug: str,
       owner_id: Optional[str] = None
   ) -> Tenant:
       ...

Documentation
^^^^^^^^^^^^^

Update documentation for all new features:

.. code-block:: bash

   # Build docs locally
   cd docs
   make html
   
   # Open in browser
   open build/html/index.html

Contribution Guidelines
-----------------------

Pull Request Process
^^^^^^^^^^^^^^^^^^^^

1. Create a feature branch:

.. code-block:: bash

   git checkout -b feature/my-new-feature

2. Make your changes with clear commits:

.. code-block:: bash

   git commit -m "Add feature: description"

3. Push to your fork:

.. code-block:: bash

   git push origin feature/my-new-feature

4. Open a Pull Request with:

   - Clear description of changes
   - Link to related issues
   - Test coverage
   - Documentation updates

Code Style
^^^^^^^^^^

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Keep functions focused and small
- Add logging for important operations

Commit Messages
^^^^^^^^^^^^^^^

Use conventional commit format:

.. code-block:: text

   feat: add custom domain batch operations
   fix: resolve R2 upload timeout issue
   docs: update configuration examples
   test: add tests for tenant deletion
   refactor: simplify storage adapter interface

Testing Guidelines
------------------

Writing Tests
^^^^^^^^^^^^^

.. code-block:: python

   import pytest
   from cloudflare_saas import CloudflareSaaSPlatform, Config

   @pytest.mark.asyncio
   async def test_create_tenant():
       config = Config(...)
       platform = CloudflareSaaSPlatform(config)
       
       tenant = await platform.create_tenant("Test", "test")
       
       assert tenant.tenant_id == "tenant-test"
       assert tenant.name == "Test"

Test Coverage
^^^^^^^^^^^^^

Maintain >90% test coverage:

.. code-block:: bash

   make test-cov

Areas to Contribute
-------------------

Current Needs
^^^^^^^^^^^^^

- Additional storage adapters (Redis, DynamoDB)
- More comprehensive error handling
- Performance optimizations
- Additional examples and tutorials
- Documentation improvements

Feature Requests
^^^^^^^^^^^^^^^^

Before starting work on a major feature:

1. Open an issue to discuss
2. Wait for maintainer feedback
3. Create a design document if needed
4. Implement with tests

Bug Reports
^^^^^^^^^^^

Good bug reports include:

- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Minimal code example

Release Process
---------------

Versioning
^^^^^^^^^^

We use Semantic Versioning:

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

Creating a Release
^^^^^^^^^^^^^^^^^^

1. Update version in ``__init__.py``
2. Update CHANGELOG.md
3. Create git tag
4. Build and publish to PyPI

Community
---------

- GitHub Issues: Bug reports and feature requests
- Discussions: Questions and ideas
- Discord: Real-time community chat (link TBD)

License
-------

By contributing, you agree that your contributions will be licensed under the same license as the project.

Code of Conduct
---------------

Be respectful and inclusive. We follow the `Contributor Covenant <https://www.contributor-covenant.org/>`_.

Questions?
----------

Feel free to open an issue or discussion if you have questions about contributing!
