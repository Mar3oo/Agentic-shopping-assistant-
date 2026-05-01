$BaseUrl = "http://127.0.0.1:8000"

$guest = Invoke-RestMethod -Method Post -Uri "$BaseUrl/users/guest"
$userId = $guest.data.user_id

$recommendation = Invoke-RestMethod -Method Post -Uri "$BaseUrl/recommendation/start" -ContentType "application/json" -Body (@{
    user_id = $userId
    message = "I need a gaming laptop under 1500 dollars"
} | ConvertTo-Json)

$recommendationChat = Invoke-RestMethod -Method Post -Uri "$BaseUrl/recommendation/chat" -ContentType "application/json" -Body (@{
    user_id = $userId
    session_id = $recommendation.session_id
    message = "why did you choose these options?"
} | ConvertTo-Json)

$comparison = Invoke-RestMethod -Method Post -Uri "$BaseUrl/comparison/start" -ContentType "application/json" -Body (@{
    user_id = $userId
    message = "iphone 15 vs galaxy s24"
} | ConvertTo-Json)

$review = Invoke-RestMethod -Method Post -Uri "$BaseUrl/review/start" -ContentType "application/json" -Body (@{
    user_id = $userId
    message = "iphone 15 reviews"
} | ConvertTo-Json)

$search = Invoke-RestMethod -Method Post -Uri "$BaseUrl/search/" -ContentType "application/json" -Body (@{
    user_id = $userId
    message = "best gaming laptop under 1500"
} | ConvertTo-Json)

$sessions = Invoke-RestMethod -Method Get -Uri "$BaseUrl/sessions/?user_id=$userId"
$messages = Invoke-RestMethod -Method Get -Uri "$BaseUrl/sessions/$($recommendation.session_id)/messages?user_id=$userId&limit=12"

[pscustomobject]@{
    user_id = $userId
    recommendation_session = $recommendation.session_id
    comparison_session = $comparison.session_id
    review_session = $review.session_id
    sessions_count = $sessions.data.sessions.Count
    recommendation_messages = $messages.data.messages.Count
}
