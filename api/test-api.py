import requests
import os

# URL for the API
url = "http://92.242.187.242:5000/api"

# Settings to send
data = {
    "location": {"lat": 52.5339887, "lon": 5.4428291}, 
    "style": "photograph", 
    "image_strength": 0.4, #max 0.4 min 0.2
    "seed": 123463446,
    "year": 2023
}

# Store the Paragraphica API key in the headers
headers = {
    "X-API-KEY": PLACE API KEY HERE
}

# Send the POST request
response = requests.post(url, json=data, headers=headers)

# Check if request was successful
if response.status_code == 200:
    print("Request successful")

    # Get the image file path from the response
    image_file_path = response.json().get('stability_image')
    description = response.json().get('description')
    status_report = response.json().get('status_report')

    # Download the image file
    with requests.get(image_file_path, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join('images', os.path.basename(image_file_path)), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Save the image to a static folder
    print(f"Image saved as {os.path.basename(image_file_path)}")
    print(f"Description = {description}")
    print(f"Status = {status_report}")

    # Send request to delete the image from the server
    delete_response = requests.delete(image_file_path, headers=headers)
    if delete_response.status_code == 200:
        print("Image deleted from the server")
    else:
        print("Failed to delete image from the server")

else:
    print(f"Request failed with status code {response.status_code}")