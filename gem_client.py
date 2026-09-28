import requests
import json


GEM_URL = "https://bidplus.gem.gov.in/all-bids"
GEM_DATA_URL = "https://bidplus.gem.gov.in/all-bids-data"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
)


def create_session():

    session = requests.Session()

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
    }

    # Create anonymous GeM session
    response = session.get(
        GEM_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return session


def fetch_gem_page(
    session,
    page=1,
    search="",
    sort="Bid-End-Date-Oldest"
):

    payload = {
        "page": page,
        "param": {
            "searchBid": search,
            "searchType": "fullText"
        },
        "filter": {
            "bidStatusType": "ongoing_bids",
            "byType": "all",
            "highBidValue": "",
            "byEndDate": {
                "from": "",
                "to": ""
            },
            "sort": sort
        }
    }

    post_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": (
            "application/x-www-form-urlencoded; charset=UTF-8"
        ),
        "Origin": "https://bidplus.gem.gov.in",
        "Referer": "https://bidplus.gem.gov.in/all-bids",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": USER_AGENT,
    }

    data = {
        "payload": json.dumps(
            payload,
            separators=(",", ":")
        ),
        "csrf_bd_gem_nk": session.cookies.get(
            "csrf_gem_cookie",
            ""
        )
    }

    response = session.post(
        GEM_DATA_URL,
        headers=post_headers,
        data=data,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    records = find_bid_records(result)

    if records:
        print("\n========== FIRST RAW BID ==========")
        print(json.dumps(records[0], indent=2))
        print("===================================\n")

    return result


def find_bid_records(obj):

    """
    Recursively search the GeM response
    for the list containing bid records.
    """

    if isinstance(obj, list):

        if obj and isinstance(obj[0], dict):

            # GeM bid records contain b_bid_number
            if any(
                "b_bid_number" in item
                for item in obj
                if isinstance(item, dict)
            ):
                return obj

        for item in obj:

            result = find_bid_records(item)

            if result is not None:
                return result

    elif isinstance(obj, dict):

        for value in obj.values():

            result = find_bid_records(value)

            if result is not None:
                return result

    return None


def first_value(value):
    """
    GeM frequently returns values inside one-element lists.
    Convert:
        ["abc"] -> "abc"
        [123]   -> 123
        []      -> None
    """
    if isinstance(value, list):
        if len(value) == 0:
            return None
        return value[0]

    return value


def normalize_bid(item):

    bid_number = first_value(
        item.get("b_bid_number")
    )

    parent_bid_number = first_value(
        item.get("b_bid_number_parent")
    )

    # If this is an RA, the parent is the original B-number
    if parent_bid_number:
        final_bid_number = parent_bid_number
        ra_number = bid_number
    else:
        final_bid_number = bid_number
        ra_number = None

    return {
        "bid_number": final_bid_number,

        "ra_number": ra_number,

        "title": first_value(
            item.get("b_category_name")
        ),

        "quantity": first_value(
            item.get("b_total_quantity")
        ),

        "bid_start": first_value(
            item.get("final_start_date_sort")
        ),

        "bid_end": first_value(
            item.get("final_end_date_sort")
        ),

        "ministry": first_value(
            item.get("ba_official_details_minName")
        ),

        "department": first_value(
            item.get("ba_official_details_deptName")
        ),

        "is_high_value": first_value(
            item.get("is_high_value")
        ),

        "is_custom_item": first_value(
            item.get("b_is_custom_item")
        ),

        "bid_type": first_value(
            item.get("b_bid_type")
        ),

        "gem_id": item.get("id"),

        "parent_bid_id": first_value(
            item.get("b_id_parent")
        )
    }
def fetch_tenders(
    pages=2,
    search="",
    sort="Bid-End-Date-Oldest"
):

    session = create_session()

    all_records = []

    for page in range(1, pages + 1):

        response = fetch_gem_page(
            session=session,
            page=page,
            search=search,
            sort=sort
        )

        records = find_bid_records(response)

        if not records:
            continue

        for record in records:

            normalized = normalize_bid(record)

            all_records.append(normalized)

    return all_records