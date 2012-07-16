def Preparer(value):
    """
    A preparer is called after deserialization of a value but before
    that value is validated.
    
    Any modifications to ``value`` required should be made by
    returning the modified value rather than modifying in-place.

    If no modification is required, then ``value`` should be returned
    as-is.
    """

    
def Validator(node, value):
    """
    A validator is called after preparation of the deserialized value.
    
    If ``value`` is not valid, raise a :class:`colander.Invalid`
    instance as an exception after.

    ``node`` is a :class:`colander.SchemaNode` instance, for use when
    raising a :class:`colander.Invalid` exception.
    """

class Type(object):
    def serialize(self, node, appstruct):
        """
        Serialize the :term:`appstruct` represented by ``appstruct``
        to a :term:`cstruct`.  The serialization should be composed of
        one or more objects which can be deserialized by the
        :meth:`colander.interfaces.Type.deserialize` method of this
        type.

        ``node`` is a :class:`colander.SchemaNode` instance.

        ``appstruct`` is an :term:`appstruct`.

        If ``appstruct`` is the special value :attr:`colander.null`,
        the type should serialize a null value.

        If the object cannot be serialized for any reason, a
        :exc:`colander.Invalid` exception should be raised.
        """

    def deserialize(self, node, cstruct):
        """
        Deserialze the :term:`cstruct` represented by ``cstruct`` to
        an :term:`appstruct`.  The deserialization should be composed
        of one or more objects which can be serialized by the
        :meth:`colander.interfaces.Type.serialize` method of this
        type.

        ``node`` is a :class:`colander.SchemaNode` instance.

        ``cstruct`` is a :term:`cstruct`.

        If the object cannot be deserialized for any reason, a
        :exc:`colander.Invalid` exception should be raised.
        """
        


class FileUploadTempStore(object):
    """
    The :class:`reform.FileUploadWidget` requires as its first
    argument a ``tmpstore``.  Such a tmpstore will implement this
    interface: an object implementing the FileUploadTempStore
    interface should implement the methods attached to this
    description.

    Effectively, this interface is a subset of the ``dict`` interface
    plus an additional method named ``preview_url``.  In fact, the
    simplest possible implementation of this interface is:

    .. code-block:: python

       class MemoryTmpStore(dict):
           def preview_url(self, name):
               return None

    However, the :class:`reform.FileUploadWidget` does not remove data
    from the tempstore implementation it uses (it doesn't have enough
    information to be able to do so), and it is job of the tempstore
    implementation itself to expire items which haven't been accessed
    in a while.

    Therefore, the above ``MemoryTmpStore`` implementation is
    generally unsuitable for production, as the data put into it is
    not automatically evicted over time and file upload data provided
    by untrusted users is usually unsuitable for storage in RAM.  It's
    more likely that an implementation in your application will center
    around a sessioning library (such as Beaker) that does data
    eviction and which stores file upload data in persistent storage.
    """

    def __setitem__(self, name, value):
        """
        Set a value.
        """

    def __getitem__(self, name):
        """
        Get a value.
        """

    def get(self, name, default=None):
        """
        Same as dict.get.
        """

    def __contains__(self, name):
        """
        This should return `True` if we have a value for the
        name supplied, `False` otherwise.
        """
        
    def preview_url(self, name):
        """
        Return the preview URL for the item previously placed into the
        tmpstore named ``name`` or ``None`` if there is no preview for
        ``name`` available (or if this tmpstore does not support
        previewable items).  This item should typically return a URL
        to a thumbnail image.
        """
        

    
