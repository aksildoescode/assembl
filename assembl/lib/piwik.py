import requests
from pyramid.settings import asbool

def piwik_UsersManager_userExists(piwik_url, piwik_api_token, userLogin):
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "UsersManager.userExists"
    params["userLogin"] = userLogin # Piwik has two different fields for login and email, but a user can have the same value as login and email
    result = requests.get(piwik_url, params=params, timeout=15)
    if result.status_code != 200:
        raise requests.ConnectionError()

    content = result.json()
    # print "piwik_UsersManager_userExists", content
    if not content:
        raise requests.ConnectionError()

    user_already_exists = asbool(content.get("value", False))
    return user_already_exists

def piwik_UsersManager_getUserByEmail(piwik_url, piwik_api_token, userEmail):
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "UsersManager.getUserByEmail"
    params["userEmail"] = userEmail # Piwik has two different fields for login and email, but a user can have the same value as login and email
    result = requests.get(piwik_url, params=params, timeout=15)
    if result.status_code != 200:
        raise requests.ConnectionError()

    content = result.json() # returns something like [{"login":"aaa","email":"aaa@aaa.com"}] or {"result":"error","message":"L'utilisateur 'aaa@aaa.com' est inexistant."}
    # print "piwik_UsersManager_getUserByEmail", content
    if not content:
        raise requests.ConnectionError()

    if "result" in content and content["result"] == "error":
        return False
    elif not isinstance(content, list):
        raise requests.ConnectionError()
    else:
        return content


def piwik_UsersManager_addUser(piwik_url, piwik_api_token, userLogin, password, email, alias=''):
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "UsersManager.addUser"
    params["userLogin"] = userLogin # Piwik has two different fields for login and email, but a user can have the same value as login and email
    params["password"] = password
    params["email"] = email
    if ( alias ):
        params["alias"] = alias
    result = requests.get(piwik_url, params=params, timeout=15)
    if result.status_code != 200:
        raise requests.ConnectionError()

    content = result.json()
    # print "piwik_UsersManager_addUser", content
    if not content:
        raise requests.ConnectionError()

    user_added = ("result" in content and content["result"] == "success")
    return user_added


def piwik_SitesManager_getSitesIdFromSiteUrl(piwik_url, piwik_api_token, url):
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "SitesManager.getSitesIdFromSiteUrl"
    params["url"] = url
    result = requests.get(piwik_url, params=params, timeout=15)

    if result.status_code != 200:
        raise requests.ConnectionError()
    content = result.json() # Content should be either an empty array, or an array like [{"idsite":"44"}]
    # print "piwik_SitesManager_getSitesIdFromSiteUrl", content
    if not isinstance(content, list):
        raise requests.ConnectionError()

    return content


def piwik_SitesManager_addSite(piwik_url, piwik_api_token, siteName, urls, ecommerce = '', siteSearch = '', searchKeywordParameters = '', searchCategoryParameters = '', excludedIps = '', excludedQueryParameters = '', timezone = '', currency = '', group = '', startDate = '', excludedUserAgents = '', keepURLFragments = '', param_type = '', settings = '', excludeUnknownUrls = ''):
    """Returns the Piwik id_site of the created website
    Warning: A new Piwik site is created everytime this method is called, even if another Piwik website already exists with the same name and URLs"""
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "SitesManager.addSite"
    params["siteName"] = siteName
    params["urls"] = urls
    if ( ecommerce ):
        params["ecommerce"] = ecommerce
    if ( siteSearch ):
        params["siteSearch"] = siteSearch
    if ( searchKeywordParameters ):
        params["searchKeywordParameters"] = searchKeywordParameters
    if ( searchCategoryParameters ):
        params["searchCategoryParameters"] = searchCategoryParameters
    if ( excludedIps ):
        params["excludedIps"] = excludedIps
    if ( excludedQueryParameters ):
        params["excludedQueryParameters"] = excludedQueryParameters
    if ( timezone ):
        params["timezone"] = timezone
    if ( currency ):
        params["currency"] = currency
    if ( group ):
        params["group"] = group
    if ( startDate ):
        params["startDate"] = startDate
    if ( excludedUserAgents ):
        params["excludedUserAgents"] = excludedUserAgents
    if ( keepURLFragments ):
        params["keepURLFragments"] = keepURLFragments
    if ( param_type ):
        params["type"] = param_type
    if ( settings ):
        params["settings"] = settings
    if ( excludeUnknownUrls ):
        params["excludeUnknownUrls"] = excludeUnknownUrls

    result = requests.get(piwik_url, params=params, timeout=15)

    if result.status_code != 200:
        raise requests.ConnectionError()

    content = result.json() # Content should be something like {"value": 47}
    # print "piwik_SitesManager_addSite", content

    if not content:
        raise requests.ConnectionError()

    if "value" in content:
        return content['value']
    return False


def piwik_UsersManager_setUserAccess(piwik_url, piwik_api_token, userLogin, access, idSites):
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "UsersManager.setUserAccess"
    params["userLogin"] = userLogin
    params["access"] = access
    params["idSites"] = idSites
    result = requests.get(piwik_url, params=params, timeout=15)

    if result.status_code != 200:
        raise requests.ConnectionError()
    content = result.json() # Content should be either an empty array, or an array like [{"idsite":"44"}]
    # print "piwik_UsersManager_setUserAccess", content

    if not content:
        raise requests.ConnectionError()

    user_access_is_set = ("result" in content and content["result"] == "success")
    return user_access_is_set


def piwik_UsersManager_hasSuperUserAccess(piwik_url, piwik_api_token, userLogin):
    params = {
        "module": "API",
        "format": "JSON",
        "token_auth": piwik_api_token
    }
    params["method"] = "UsersManager.hasSuperUserAccess"
    params["userLogin"] = userLogin

    result = requests.get(piwik_url, params=params, timeout=15)

    if result.status_code != 200:
        raise requests.ConnectionError()
    content = result.json() # Content should be like {"value": true}
    # print "piwik_UsersManager_hasSuperUserAccess", content

    if not content:
        raise requests.ConnectionError()

    return asbool(content.get("value", False))


