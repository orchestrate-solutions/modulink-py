"""
Context type for ModuLink Next.

Defines the Context type used throughout the system.
Context is mutable by default, but can be made immutable via .asImmutable().
See README.md section 2.1 for details.
"""

class Context(dict):
    """
    ModuLink Next Context (mutable by default).

    - Behaves like a standard Python dict for all read/write operations.
    - Use .asImmutable() to get an immutable version (ImmutableContext).
    - Use .asMutable() to get a mutable version (Context).
    - Use .isMutable() and .isImmutable() to check mutability.
    - Designed for seamless use in both functional and imperative workflows.
    - Supports all standard dict methods and iteration.
    - Use for passing state between links in a Chain.
    """
    def isMutable(self):
        """Return True if this context is mutable (default)."""
        return True

    def isImmutable(self):
        """Return True if this context is immutable (always False for Context)."""
        return False

    def asImmutable(self):
        """Return an immutable version of this context (ImmutableContext)."""
        return ImmutableContext(self)

    def asMutable(self):
        """Return self (already mutable)."""
        return self

class ImmutableContext(Context):
    """
    ModuLink Next ImmutableContext (read-only).

    - Behaves like a dict for all read operations, but blocks all mutation.
    - Use .asMutable() to get a mutable copy (Context).
    - Use .isMutable() and .isImmutable() to check mutability.
    - All mutation methods (set, del, update, pop, etc.) raise TypeError.
    - Use for safety in async/concurrent or functional workflows.
    - Designed to prevent accidental state changes.
    """
    def __setitem__(self, key, value):
        """Raise TypeError: ImmutableContext does not support item assignment."""
        raise TypeError("ImmutableContext does not support item assignment")

    def __delitem__(self, key):
        """Raise TypeError: ImmutableContext does not support item deletion."""
        raise TypeError("ImmutableContext does not support item deletion")

    def clear(self):
        """Raise TypeError: ImmutableContext does not support clear()."""
        raise TypeError("ImmutableContext does not support clear()")

    def pop(self, key, default=None):
        """Raise TypeError: ImmutableContext does not support pop()."""
        raise TypeError("ImmutableContext does not support pop()")

    def popitem(self):
        """Raise TypeError: ImmutableContext does not support popitem()."""
        raise TypeError("ImmutableContext does not support popitem()")

    def setdefault(self, key, default=None):
        """Raise TypeError: ImmutableContext does not support setdefault()."""
        raise TypeError("ImmutableContext does not support setdefault()")

    def update(self, *args, **kwargs):
        """Raise TypeError: ImmutableContext does not support update()."""
        raise TypeError("ImmutableContext does not support update()")

    def isMutable(self):
        """Return False (ImmutableContext is not mutable)."""
        return False

    def isImmutable(self):
        """Return True (ImmutableContext is immutable)."""
        return True

    def asImmutable(self):
        """Return self (already immutable)."""
        return self

    def asMutable(self):
        """Return a mutable copy of this context (Context)."""
        return Context(self)
