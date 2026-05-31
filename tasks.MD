The class `Item` has an attribute `archive` that is deprecated and to be removed/ In its place is the attribute Llibrary which
can have values from `class Library(ModelEnum)`
Find all usages of the `archive` attribute in views, forms and templates and change them to use `location`. 
Some staff views are already correct
In public views only items with Location.SHOP or location.ARCHIVE are to be displayed.Items with Location.RESEARCH
are only visible in staff views.

