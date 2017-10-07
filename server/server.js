require('./config/config');
const express = require('express');
const bodyParser = require('body-parser');
var path = require('path');
var multer = require('multer');

const port = process.env.PORT;
let app = express();

/* Configuration */

var storage = multer.diskStorage({
    destination: function (req, file, callback) {
        callback(null, './uploads')
    },
    filename: function (req, file, callback) {
        console.log(file)
        callback(null, file.fieldname + '-' + Date.now() + path.extname(file.originalname))
    }
});

/*
TODO: Change it
*/
app.get('/api/file', function (req, res) {
    res.render('index')
})


app.post('/api/file', function (req, res) {
    var upload = multer({
        storage: storage
    }).single('userFile')
    upload(req, res, function (err) {
        res.end('File is uploaded')
    })
})


app.listen(port, () => {
    console.log(`Server running successfully on port: ${port}`);
})
