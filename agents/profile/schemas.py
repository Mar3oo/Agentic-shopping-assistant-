from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class UserProfile(BaseModel):
    product_category: Optional[str] = Field(
        None, description="Type of product (laptop, phone, etc.)"
    )
    product_intent: Optional[str] = Field(
        None, description="What the user wants to use the product for"
    )
    budget: Optional[str] = Field(None, description="Budget range provided by the user")

    # country: Optional[str] = Field(
    #     None, description="User country for market-specific search"
    # )

    user_type: Optional[str] = Field(
        None, description="Type of user (student, parent, gamer, professional)"
    )
    target_user: Optional[str] = Field(
        None, description="Who the product is for (self, son, daughter, etc.)"
    )

    usage_intensity: Optional[str] = Field(
        None, description="Expected usage level (light, medium, heavy)"
    )

    priorities: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Importance weights like performance, battery, camera (0–1)",
    )

    must_have_features: Optional[List[str]] = Field(
        default_factory=list,
        description="Features that must exist (e.g., SSD, 16GB RAM)",
    )
    nice_to_have_features: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional features",
    )

    preferences: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Extra preferences like RAM, brand, size, etc.",
    )
    search_queries: Optional[List[str]] = Field(
        default_factory=list,
        description="Generated search queries for scraping",
    )


class ProfileAgentOutput(BaseModel):
    profile: UserProfile
    # missing_fields: List[str]
    # is_complete: bool
    # next_question: Optional[str] = None
    # choices: Optional[List[str]] = None
