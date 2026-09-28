from fastapi import FastAPI, Query
from gem_client import fetch_tenders


app = FastAPI(
    title="GeM Tender API",
    description="API for retrieving GeM tenders and bids",
    version="1.0.0"
)


@app.get("/")
def root():

    return {
        "message": "GeM Tender API is running"
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/tenders")
def get_tenders(
    page: int = Query(
        default=1,
        ge=1,
        le=10
    ),

    search: str = Query(
        default=""
    ),

    sort: str = Query(
        default="Bid-End-Date-Oldest"
    )
):

    try:

        tenders = fetch_tenders(
            pages=page,
            search=search,
            sort=sort
        )

        return {
            "success": True,
            "count": len(tenders),
            "tenders": tenders
        }

    except Exception as e:

        return {
            "success": False,
            "count": 0,
            "tenders": [],
            "error": str(e)
        }