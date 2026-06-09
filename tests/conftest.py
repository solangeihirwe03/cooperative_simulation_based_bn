"""
conftest.py — imported automatically by pytest before any test module.

SQLAlchemy resolves relationships lazily by string name (e.g. "Member").
If only some models are imported, mapper initialisation fails with
  InvalidRequestError: expression 'Member' failed to locate a name.

Importing every model here guarantees the mapper is fully configured
before tests that instantiate model objects (like Penalty(...)) run.
"""

# Trigger SQLAlchemy mapper registration for every model in the project.
import app.models.cooperatives        # noqa: F401
import app.models.members             # noqa: F401
import app.models.policies            # noqa: F401
import app.models.loans               # noqa: F401
import app.models.payments            # noqa: F401
import app.models.penalties           # noqa: F401
import app.models.member_contributions  # noqa: F401
import app.models.scenario            # noqa: F401
