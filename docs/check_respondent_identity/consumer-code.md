# Check Respondent Identity - Consumer Code

This document captures the JavaScript blocks embedded in surveys that consume the `check_respondent_identity` service. Each block is included as provided, followed by a brief explanation.

## 1) `phone_validator`

Checks if a respondent is qualified using country, phone number, and project type. It stores the result in `isRespondentAuthorized` (`1` for authorized, `2` for not authorized).

```javascript
function callApi(url) {
    var request = new XMLHttpRequest();
    request.open("GET", url, false); // `false` makes the request synchronous
    request.send(null);

    if (request.status === 200) {
        return { isAuthorized: true, payload: JSON.parse(request.responseText) };
    } else {
        console.warn("Request failed with status code:", request.status);
        return { isAuthorized: false, payload: null };
    }
}

const baseServiceURL = "https://service-check-respondent-identity-384349768580.us-central1.run.app/check_respondent_qualified";
const phoneNumber = $survey.getSelectedOption('TEL.1.1');
const projectType = $survey.getSelectedOption('project_type');
const country = $survey.getSelectedOption('country');

const url = baseServiceURL + "/" + country + "/" + phoneNumber + "/" + projectType;
const apiResult = callApi(url);
console.log(apiResult.payload)

if (apiResult.isAuthorized) {
    $survey.setOptionSelected("isRespondentAuthorized", 1); // Authorized
} else {
    $survey.setOptionSelected("isRespondentAuthorized", 2); // Not authorized
}

// const isAuthorizedValue = $survey.getSelectedOption("isRespondentAuthorized");
// console.log("Is Respondent Authorized?", isAuthorizedValue);
// console.log("Payload Data:", apiResult.payload);
```

## 2) `verification_code`

Sends an SMS verification code to the respondent phone number using `country` and `TEL.1.1`.

```javascript
function callApi(url) {
    var request = new XMLHttpRequest();
    request.open("GET", url, false); // `false` makes the request synchronous
    request.send(null);

    if (request.status === 200) {
        return { isAuthorized: true, payload: JSON.parse(request.responseText) };
    } else {
        console.warn("Request failed with status code:", request.status);
        return { isAuthorized: false, payload: null };
    }
}

const baseServiceURL = "https://service-check-respondent-identity-384349768580.us-central1.run.app/send_code";
const phoneNumber = $survey.getSelectedOption('TEL.1.1');
const country = $survey.getSelectedOption('country');

const url = baseServiceURL + "/" + country + "/" + phoneNumber
const apiResult = callApi(url);
console.log(apiResult.payload)

// console.log("Payload Data:", apiResult.payload);
```

## 3) `code_validator`

Validates the first code entered by the respondent (`verification_code`). It stores result in `isCodeValid` (`1` valid, `2` invalid).

```javascript
function callApi(url) {
    var request = new XMLHttpRequest();
    request.open("GET", url, false); // `false` makes the request synchronous
    request.send(null);

    if (request.status === 200) {
        return { isAuthorized: true, payload: JSON.parse(request.responseText) };
    } else {
        console.warn("Request failed with status code:", request.status);
        return { isAuthorized: false, payload: null };
    }
}

const baseServiceURL = "https://service-check-respondent-identity-384349768580.us-central1.run.app/verify";
const phoneNumber = $survey.getSelectedOption('TEL.1.1');
const verificationCode = $survey.getSelectedOption('verification_code');
const country = $survey.getSelectedOption('country');

const url = baseServiceURL + "/" + country + "/" + phoneNumber + "/" + verificationCode;
const apiResult = callApi(url);
console.log(apiResult.payload)

if (apiResult.isAuthorized) {
    $survey.setOptionSelected("isCodeValid", 1); // Authorized
} else {
    $survey.setOptionSelected("isCodeValid", 2); // Not authorized
}

// const isValidValue = $survey.getSelectedOption("isCodeValid");
// console.log("Is Code Valid?", isValidValue);
// console.log("Payload Data:", apiResult.payload);
```

## 4) `supervisor_verification_code`

Sends a WhatsApp verification code only if the phone number belongs to an active field supervisor in the Firestore document `settings/business_data`. The `supervisor=true` query parameter enables this validation.

The service returns `403` when the phone number is not an active supervisor. This response must not fall back to the regular SMS endpoint, because that would send a code to an unauthorized supervisor number.

```javascript
function callApi(url) {
    var request = new XMLHttpRequest();
    request.open("GET", url, false); // `false` makes the request synchronous
    request.send(null);

    return {
        isAuthorized: request.status === 200,
        status: request.status,
        payload: request.responseText
            ? JSON.parse(request.responseText)
            : null
    };
}

const baseServiceURL = "https://service-check-respondent-identity-384349768580.us-central1.run.app/send_wp_code";
const phoneNumber = $survey.getSelectedOption('TEL.1.1');
const country = $survey.getSelectedOption('country');

const url = baseServiceURL + "/" + country + "/" + phoneNumber + "?supervisor=true";
const apiResult = callApi(url);
console.log(apiResult.payload);

if (apiResult.isAuthorized) {
    console.log("Supervisor WhatsApp code sent", apiResult.payload);
} else if (apiResult.status === 403) {
    console.warn("Phone number is not an active supervisor");
} else {
    console.warn("Failed to send supervisor WhatsApp code");
}
```

## 5) `code_validator_2`

Validates a second code input (`verification_code_2`) and stores result in `isCodeValid_2` (`1` valid, `2` invalid).

```javascript
function callApi(url) {
    var request = new XMLHttpRequest();
    request.open("GET", url, false); // `false` makes the request synchronous
    request.send(null);

    if (request.status === 200) {
        return { isAuthorized: true, payload: JSON.parse(request.responseText) };
    } else {
        console.warn("Request failed with status code:", request.status);
        return { isAuthorized: false, payload: null };
    }
}

const baseServiceURL = "https://service-check-respondent-identity-384349768580.us-central1.run.app/verify";
const phoneNumber = $survey.getSelectedOption('TEL.1.1');
const verificationCode = $survey.getSelectedOption('verification_code_2');
const country = $survey.getSelectedOption('country');

const url = baseServiceURL + "/" + country + "/" + phoneNumber + "/" + verificationCode;
const apiResult = callApi(url);
console.log(apiResult.payload)

if (apiResult.isAuthorized) {
    $survey.setOptionSelected("isCodeValid_2", 1); // Authorized
} else {
    $survey.setOptionSelected("isCodeValid_2", 2); // Not authorized
}

// const isValidValue = $survey.getSelectedOption("isCodeValid_2");
// console.log("Is Code Valid?", isValidValue);
// console.log("Payload Data:", apiResult.payload);
```

## 6) `REF.1` (typical) / Data Submission

If respondent is marked authorized, this block sends respondent data to `write_respondent` using `POST` JSON.

```javascript
const isAuthorizedValue = $survey.getSelectedOption("isRespondentAuthorized") === 'true';

if (isAuthorizedValue) {
    const url = 'https://service-check-respondent-identity-384349768580.us-central1.run.app/write_respondent';

    const payload = {
        country: $survey.getSelectedOption('country'),
        phone_number: $survey.getSelectedOption('TEL.1.1'),
        name: $survey.getSelectedOption('Nom.1'),
        age: $survey.getSelectedOption('age'),
        gender: $survey.getSelectedOption('gender'),
        project_type: $survey.getSelectedOption('project_type'),
        study_id: $survey.getSelectedOption('study_id'),
    };

    fetch(url, {
        method: 'POST', // Specify the HTTP method
        headers: {
            'Content-Type': 'application/json', // Set the content type
        },
        body: JSON.stringify(payload), // Convert the payload to JSON
    })
        .then(data => {
            console.log('Success:', data);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
```
