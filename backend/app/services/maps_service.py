"""
Google Maps integration: reverse geocoding, directions, and nearby
place search (NGOs / vets / hospitals).

Requires GOOGLE_MAPS_API_KEY with the Geocoding, Directions, and
Places APIs enabled on the Google Cloud project.
"""
from __future__ import annotations

import httpx

from app.config import settings


class MapsNotConfigured(RuntimeError):
    pass


class MapsRequestError(RuntimeError):
    pass


async def reverse_geocode(latitude: float, longitude: float) -> str | None:
    if not settings.google_maps_api_key:
        raise MapsNotConfigured("GOOGLE_MAPS_API_KEY is not configured.")

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{latitude},{longitude}", "key": settings.google_maps_api_key}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise MapsRequestError(f"Geocoding request failed ({response.status_code}).")

    data = response.json()
    results = data.get("results") or []
    return results[0]["formatted_address"] if results else None


async def get_directions(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> dict:
    if not settings.google_maps_api_key:
        raise MapsNotConfigured("GOOGLE_MAPS_API_KEY is not configured.")

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "key": settings.google_maps_api_key,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise MapsRequestError(f"Directions request failed ({response.status_code}).")

    data = response.json()
    routes = data.get("routes") or []
    if not routes:
        return {"distance_text": None, "duration_text": None, "polyline": None}

    leg = routes[0]["legs"][0]
    return {
        "distance_text": leg["distance"]["text"],
        "duration_text": leg["duration"]["text"],
        "polyline": routes[0]["overview_polyline"]["points"],
    }


async def find_nearby_places(latitude: float, longitude: float, place_type: str, radius_m: int = 5000) -> list[dict]:
    """place_type e.g. 'veterinary_care', 'animal_shelter'."""
    if not settings.google_maps_api_key:
        raise MapsNotConfigured("GOOGLE_MAPS_API_KEY is not configured.")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius_m,
        "type": place_type,
        "key": settings.google_maps_api_key,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise MapsRequestError(f"Nearby search failed ({response.status_code}).")

    data = response.json()
    return [
        {
            "name": place.get("name"),
            "address": place.get("vicinity"),
            "latitude": place["geometry"]["location"]["lat"],
            "longitude": place["geometry"]["location"]["lng"],
            "rating": place.get("rating"),
        }
        for place in data.get("results", [])
    ]
