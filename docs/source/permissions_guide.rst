Cloudflare API Token Permissions Guide
========================================

Token Types Overview
--------------------

Global API Key (Legacy - Not Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Scope**: Full account access
- **Usage**: Can do everything in your account
- **Security**: Less secure, no granular control
- **Use Case**: Creating API tokens programmatically

API Token (Recommended - What We Need)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Scope**: Granular permissions
- **Types**:

  - **User Token**: Can have both Account AND Zone permissions (✅ This is what we need)
  - **Account Token**: Only Account-level permissions
  - **Zone Token**: Only Zone-level permissions

- **Security**: More secure, follows principle of least privilege

What We Need: User API Token
----------------------------

For the Cloudflare SaaS platform, we need a **User API Token** with:

- ✅ Account-level permissions (for R2, Workers)
- ✅ Zone-level permissions (for DNS, Custom Hostnames, Worker Routes)

**Why not Account Token?** Because we need both Account AND Zone permissions.

Required Permissions Breakdown
------------------------------

Account-Level Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^

These apply to the entire Cloudflare account (ID: ``6451353ea5a8407bab6162abc42f5338``):

.. list-table:: Account-Level Permissions
   :header-rows: 1
   :widths: 30 35 35

   * - Permission
     - Why We Need It
     - Required For
   * - ``Account:Read``
     - Read account information
     - Platform initialization, validation
   * - ``Account:Cloudflare R2:Edit``
     - Create/manage R2 buckets and objects
     - Storing tenant static files
   * - ``Account:Cloudflare Workers:Edit``
     - Deploy/manage Worker scripts
     - Site routing, tenant resolution

**Resource Scope**: All accounts (or specific account ID)

Zone-Level Permissions
^^^^^^^^^^^^^^^^^^^^^^

These apply to specific zone (ID: ``2cf1f02313c4ef76af3d62eb78bb906e``):

.. list-table:: Zone-Level Permissions
   :header-rows: 1
   :widths: 30 35 35

   * - Permission
     - Why We Need It
     - Required For
   * - ``Zone:Read``
     - Read zone settings and configuration
     - Domain verification, DNS checks
   * - ``Zone:Cloudflare Workers Routes:Edit``
     - Configure Worker routes
     - Routing requests to Worker script
   * - ``Zone:Custom Hostnames:Edit``
     - Add/verify custom domains
     - Multi-tenant custom domain support

**Resource Scope**: Specific zone (your platform domain zone)

Permission Hierarchy
--------------------

::

   User API Token (Created at User level)
   ├── Account Permissions
   │   ├── Account:Read
   │   ├── Account:Cloudflare R2:Edit
   │   └── Account:Cloudflare Workers:Edit
   └── Zone Permissions (for specific zone)
       ├── Zone:Read
       ├── Zone:Cloudflare Workers Routes:Edit
       └── Zone:Custom Hostnames:Edit

Current Token Status (As of Testing)
------------------------------------

Based on ``test_token_permissions.py`` results:

✅ **Working** (4/8):

- Basic Auth
- Account Access
- R2 Buckets List
- R2 Bucket Create

❌ **Missing** (4/8):

- Zone Access (needs ``Zone:Read``)
- Workers List (needs ``Account:Cloudflare Workers:Edit``)
- Workers Routes (needs ``Zone:Cloudflare Workers Routes:Edit``)
- Custom Hostnames (needs ``Zone:Custom Hostnames:Edit``)

How to Create the Token
-----------------------

Option 1: Using Global API Key (Programmatic)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the script: ``create_token_with_global_key.py``

.. code-block:: bash

   python create_token_with_global_key.py \
     --email your@email.com \
     --global-key your_global_api_key \
     --account-id 6451353ea5a8407bab6162abc42f5338 \
     --zone-id 2cf1f02313c4ef76af3d62eb78bb906e

Option 2: Manual Creation (Cloudflare Dashboard)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Create Token → Create Custom Token
3. Add all permissions listed above
4. Set account and zone resources
5. Create and copy token

Option 3: Using Existing Token with Token Creation Permission
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the script: ``create_cloudflare_token.py``
(Requires existing token with ``User:API Tokens:Edit`` permission)

Security Best Practices
-----------------------

1. **Never use Global API Key** in production applications
2. **Rotate tokens** periodically
3. **Use environment variables** for token storage
4. **Set token expiration** (TTL) when possible
5. **Monitor token usage** in Cloudflare dashboard
6. **Revoke unused tokens** immediately

Troubleshooting
---------------

Error: "Authentication error (10000)"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Token lacks the specific permission for that operation
- Add the missing permission to your token

Error: "Unauthorized to access requested resource (9109)"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Token doesn't have access to the account or zone
- Verify account ID and zone ID in token resources
- Check token scope includes both Account and Zone

Token works for R2 but not Workers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Token has Account R2 permissions but lacks Workers permissions
- Add ``Account:Cloudflare Workers:Edit`` to token

Token works for account but not zone
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Token may be an "Account Token" instead of "User Token"
- Create a new User Token with both Account and Zone permissions