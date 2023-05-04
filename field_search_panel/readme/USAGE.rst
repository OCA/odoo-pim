If you want a model search view to have a dynamic search panel, this model need to inherit from 'search.panel.mixin'.

You are not obliged to define a search panel in the xml view, but if you do so the fields that were defined in the xml view will be used to build the search panel in combination with the fields that will be define at run time. The fields define in the xml view won't be removable at run time.

To define the field you want to be display at run time *Settings* > *Search panel fields* than select the fields you want to be display at run time. Be careful, select fields of model that inherit from 'search.panel.mixin' or they won't be display.
