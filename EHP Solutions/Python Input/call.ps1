$url = "http://192.168.100.229:5000/process_data"
$jsonBody = @{
    memberships = @(
        @{
            ID = 1
            FirstName = "John"
            LastName = "Doe"
            BirthDate = "1980-01-15"
            Year = 14
        },
        @{
            ID = 2
            FirstName = "Jane"
            LastName = "Smith"
            BirthDate = "1975-05-20"
            Year = 17
        }
    )
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri $url -Method Post -Body $jsonBody -ContentType "application/json"
$response | ConvertTo-Json
