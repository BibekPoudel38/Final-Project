import graphene
import inventory.schema  # Import the schema we created in the previous step

import sales.schema


# Inherit from the Inventory Query
class Query(inventory.schema.Query, sales.schema.Query, graphene.ObjectType):
    # If you had other apps (e.g., 'users'), you would inherit their queries here too
    # class Query(inventory.schema.Query, users.schema.Query, ...):
    pass


# This is the variable Django needs to see
schema = graphene.Schema(query=Query)
