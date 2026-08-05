def check_server_status(servers):
    # Missing the requests import!
    for i in range(len(servers)):
        response = requests.get(servers[i])
        print(response.status_code)