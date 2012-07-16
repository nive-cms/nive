Reform
======
A Python HTML form library.

The reform package is a merge of deform and colander and includes several changes 
to make form handling easier:

- form processing and data validation is based on dictionaries and not
  on positional form values. This means forms can easily build manually or faked by js
  ajax calls without restrictions. You can also use cUrl or similar to
  submit form data.
- MappingWidget and SequenceWidget have been removed
- colander has been moved to reform.schema  
- You can use form.Form directly to add new schema nodes without creating a schema 
  yourself
- code widget has been added (including codemirror editor)

  
Please see
http://docs.pylonsproject.org/projects/deform/dev/ for the documentation.

