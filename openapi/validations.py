def exists_info_title(openapi):
    info_title = openapi.get('info', {}).get('title')
    if not info_title:
        return False

    return True
