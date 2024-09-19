import uuid

import requests

# URL for inserting a user
insert_url = 'http://localhost:5001'
# insert_url = 'https://prognostic-ai-backend-acab284a2f57.herokuapp.com'

# Generate a UUID for the user
user_id = str(uuid.uuid4())
user_email = "lukasz.senderowski+16@example.com"
data = {
    "user_email": user_email,
    "text": "<h1>From AI-Powered Books to AI-Powered Marketing: Unleash Your Full Potential</h1><br><br><p>Kyle, you're already harnessing the power of AI to transform entrepreneurs' ideas into compelling books. But what if you could apply that same revolutionary approach to *every aspect* of your marketing?</p><br><br><p>Your innovative use of AI for storytelling shows you understand the <strong>game-changing potential</strong> of this technology. Now, imagine extending that power beyond books to create *personalized, laser-targeted marketing* for each of your leads.</p><br><br><h2>The Next Frontier in AI Marketing</h2><br><br><p>Just as you've eliminated the struggle of writing a book, you could eliminate the guesswork in your marketing. Picture an AI that analyzes each lead, crafting *tailored messages* that resonate on a deeply personal level.</p><br><br><p>This isn't just about efficiency – it's about <strong>exponential growth</strong>. By personalizing every interaction, you could see conversion rates soar and client acquisition costs plummet.</p><br><br><h2>From Author to Marketing Mastermind</h2><br><br><p>You've already proven that AI can capture an entrepreneur's unique voice. Now, let that same technology *amplify your marketing voice*, speaking directly to each potential client's needs and desires.</p><br><br><p>Ready to write the next chapter in your AI success story? The future of personalized marketing is waiting for you to claim it.</p><br>",

}

# Make the POST request to insert the user
print(f'{insert_url}/insert_user')
print(data)
response = requests.post(f'{insert_url}/insert_user', json=data)

# Print the response from the POST request
print("POST Request:")
print(response.status_code)
print(response.json())

# For retrieving the user data, we will use POST and send the email in the request body
get_data = {
    "user_email": user_email
}

# Make the POST request to retrieve the user data
get_response = requests.post(f'{insert_url}/get_user', json=get_data)

# Print the response from the POST request
print("\nGET Request:")
print(get_response.status_code)
print(get_response.json())
