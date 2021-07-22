const express = require('express');
const cors = require('cors');
const path = require('path')

const app = express();

app.use(cors());
app.use(express.static(__dirname));


app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname + '/index.html'))
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`listening on port ${PORT}`));