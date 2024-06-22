function defaultErrorHandle(error) {
    $("#error-box").append(error);
}

function sendGet(path, callback, errorHandle) {
    if(errorHandle != null) {
        $.get(path, callback).fail(errorHandle)
    }
    else {
        $.get(path, callback).fail(defaultErrorHandle)
    }
}

function sendPost(path, data, callback, errorHandle) {
    if(errorHandle != null) {
        $.ajax(
        {
            type: "POST",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            url: path,
            data: JSON.stringify(data),
            error: errorHandle,
            success: callback
        });
    }
    else {
        $.ajax(
        {
            type: "POST",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            url: path,
            data: JSON.stringify(data),
            error: defaultErrorHandle,
            success: callback
        });
    }
}

function sendPatch(path, data, callback, errorHandle) {
    if(errorHandle != null) {
        $.ajax(
        {
            type: "PATCH",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            url: path,
            data: JSON.stringify(data),
            error: errorHandle,
            success: callback
        });
    }
    else {
        $.ajax(
        {
            type: "PATCH",
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            url: path,
            data: JSON.stringify(data),
            error: defaultErrorHandle,
            success: callback
        });
    }
}