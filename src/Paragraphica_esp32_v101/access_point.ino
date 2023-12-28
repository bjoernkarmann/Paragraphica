String getForm(const Replacement replacements[], size_t length) {
    String form = R"rawliteral(

    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8" />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, maximum-scale=1, minimum-scale=1, user-scalable=no, minimal-ui"
        />
        <style>
          body,
          select,
          input[type="text"],
          input[type="password"],
          input[type="submit"],
          input[type="button"] {
            font-size: 14px;
            font-family: verdana;
            text-align: center;
          }
          body {
            background: #111;
            color: #fff;
          }
          form {
            margin: 0 auto;
            width: 300px;
          }
          select,
          input[type="text"],
          input[type="password"] {
            width: 100%;
            height: 45px;
            margin: 10px 0px;
            border-radius: 30px;
            border: 0;
          }
          input[type="submit"] {
            padding: 10px 10px;
            color: #fff;
            border: none;
            cursor: pointer;
            border-radius: 30px;
            background: #c31919;
          }
          .gray {
            color: rgb(120, 120, 120);
          }
        </style>
      </head>

      <body>
        <form id="wifiForm" method="POST" action="/setup">
          <p>Enter your hotspot <br />or wifi details</p>
          <p style="color: #c31919">{{error}}</p>
          <p style="color: #19c38d">{{success}}</p>
          NETWORK:
          <select id="network" name="ssid">
            <option value="">Select a network</option>
            {%SSID_LIST%}</select
          ><br /><br />
          PASSWORD:
          <input id="password" type="password" name="password" />
          <br /><br />
          <input type="submit" value="CONNECT" />
          <br /><br />
          <p class="gray">
            Paragraphica needs an internet connection to gather location data for
            the image generation process. Hotspot- or wifi details are securely
            stored on the device.
          </p>
          <a class="gray" href="#">Privacy Policy</a>
        </form>

        <script>
          document.getElementById("wifiForm").onsubmit = function () {
            return !(
              document.getElementById("network").value === "" ||
              document.getElementById("password").value === ""
            );
          };
        </script>
      </body>
    </html>


    )rawliteral";

    // Replace the placeholders with actual values
    for (size_t i = 0; i < length; i++) {
        form.replace(replacements[i].placeholder, replacements[i].value);
    }

    return form;
}