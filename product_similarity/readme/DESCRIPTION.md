This module lets you define the product characteristics used to represent
each product as a vector, as a base to compute a similarity score between
products (e.g. for product recommendations).

Each *Product Vector Characteristic* links a field of `product.product`
(boolean, selection, many2one or many2many), and for non boolean fields one
of its possible values, to a dimension (index) of the vector and a weight
used when computing distances between vectors.
