module.exports.handler = async (event) => {
    try {
        const{
            weight,
            height,
            age,
            gender
        } = JSON.parse(event.body)

        BMR = 0
        //Men: BMR = 88.362 + (13.397 x weight in kg) + (4.799 x height in cm) – (5.677 x age in years)
        //Women: BMR = 447.593 + (9.247 x weight in kg) + (3.098 x height in cm) – (4.330 x age in years)
        if (gender == 'male') {
            BMR = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        } else {
            BMR = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        }

        return {
                statusCode: 200,
                headers: {
                "Content-Type": "application/json",
                'Access-Control-Allow-Origin' : '*',
                'Access-Control-Allow-Credentials': '*'
                },
                body: JSON.stringify({ BMR })
            }
    
    } catch (error) {
        // Handle any errors that occur during the retrieval
        console.error('Error retrieving parameter:', error);
    }
}