export const successResponse = (res, data, msg = "Success", statusCode = 200) => {
    return res.status(statusCode).json({
        success: true,
        msg,
        data,
    });
};

export const errorResponse = (res, error, msg = "Error", statusCode = 500) => {
    return res.status(statusCode).json({
        success: false,
        msg: msg || error.message,
        data: null,
    });
};
