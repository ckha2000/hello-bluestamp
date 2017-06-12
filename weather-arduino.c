#include <Arduino.h>
#include <Phpoc.h>
#include <SPI.h>
#include "Timer.h"

#include <ArduinoJson.h>

static PhpocClient phpocClient;

#define INTERVAL 4000

#define HTTP_QUERY_SIZE 1400
uint8_t httpQuery[HTTP_QUERY_SIZE];

int BUTTON_GPIO = 3;

char *server = "api.openweathermap.org";
char *apiKey = "YOUR_API_KEY";
char *cityNames[] = {"CITY_NAME,COUNTRY_CODE"};
char *currentWeather = "GET /data/2.5/weather?";

// Group 2xx: Thunderstorm  weather5.png
// Group 3xx: Drizzle  weather5.png
// Group 5xx: Rain  weather5.png

// Group 6xx: Snow  weather7.png

// Group 7xx: Atmosphere(안개)  weather2.png

// Group 800: CLEAR SKY. weather1.png

// Group 801: FEW CLOUDS. weather4.png
// Group 802: SCATTERED CLOUDS. weather2.png
// Group 803: BROKEN CLOUDS. weather3.png
// Group 804: OVERCAST CLOUDS. weather3.png

uint16_t queryLength = 0;
bool isRunning = false;
String httpResponse = "";
int numberOfCity = 0;

void setup() {
  // put your setup code here, to run once:  
  Serial.begin(115200);
  while (!Serial);// wait for serial port to connect.
  Serial.println();

  Serial1.begin(115200);
  while (!Serial1);// wait for serial port to connect.

  sendCmd("Clear\r\n");
  sendCmd("LoadFont \"/unbatang.ttf\"\r\n");

  Phpoc.begin(PF_LOG_SPI | PF_LOG_NET);
  Serial.println(Phpoc.localIP());

  numberOfCity = sizeof(cityNames) / sizeof(char*);
  
  // LCD
  initLCD();
}

void loop() {  
  // put your main code here, to run repeatedly:  
  apiLoop();
  httpLoop();
}

void apiLoop()
{
  static int index = 0;
  static unsigned long prevMills = 0;
  bool callApi = false;

  unsigned long currentMills = millis();
  if(prevMills == 0 || (currentMills - prevMills >= INTERVAL))
  {
    prevMills = currentMills;
    callApi = true;
  }

  if(callApi)
  {
    queryLength = getQueryCurrentWeather(httpQuery, cityNames[index++], apiKey);
    if(index >= numberOfCity)
      index = 0;
      
    httpResponse = "";
    if(phpocClient.connect(server, 80))
    {
      isRunning = true;
      phpocClient.write(httpQuery, queryLength);
    }
  }
}

char buf[1024];
String f = "\r\n\r\n";
void httpLoop()
{
  if(isRunning)  
  {
    uint16_t cnt = phpocClient.available();
    if(cnt > 0)
    {
      uint8_t tryRead = cnt > 128 ? 128 : cnt;
      memset(buf, 0, 1024);
      uint16_t recv = phpocClient.read(buf, tryRead);
      
      httpResponse = httpResponse + buf;      
      
      int idx = httpResponse.lastIndexOf(f);
      if(idx >= 0)
        httpResponse = httpResponse.substring(idx + 4);
    }
    
    if(!phpocClient.connected())
    {
      isRunning = false;
      sendCmd("DisableFlush");
      
      //----------------------------------------
      // JSON
      Serial.println(httpResponse.c_str());
      
      DynamicJsonBuffer jsonBuffer;
      JsonObject& root = jsonBuffer.parseObject(httpResponse);
      if(!root.success())
      {
        Serial.println("parseObject failed.");
        phpocClient.stop();
        isRunning = false;
        return;
      }
      
      uint16_t resultCode = root["cod"];
      Serial.println(resultCode);
      if(resultCode == 200)
      {
        //
        JsonObject& weather = root["weather"][0];
        String weatherId = weather["id"]; 
        String cityName = root["name"]; 
        double temperature = root["main"]["temp"]; 
        String temp = String(lround(temperature));
        String humidity = root["main"]["humidity"]; 
        String weatherDesc = weather["description"]; 

        printIcon(weatherId);
        printCity(cityName);
        printTemperature(temp);
        printHumidity(humidity);
        printWeather(weatherDesc);
        
        hidePopup();
      
        sendCmd("EnableLayer 1");
        sendCmd("EnableLayer 2");
        sendCmd("EnableLayer 3");
        sendCmd("EnableLayer 4");
        sendCmd("EnableLayer 5");
      }
      else
      {
        // fail.
      }
      //----------------------------------------
      
      Serial.println("disconnected");
      phpocClient.stop();
      sendCmd("EnableFlush");
    }
  }
}

uint16_t writeString(const char* string, uint8_t* buf, uint16_t pos) 
{
    const char* idp = string;
    uint16_t i = 0;
 
    while (*idp) 
    {
        buf[pos++] = *idp++;
        i++;
    }
    
    return pos;
}

uint16_t getQueryCurrentWeather(uint8_t* query, char* cityName, char* apiKey)
{
  uint16_t queryLength = 0;

  queryLength = writeString(currentWeather, query, queryLength);
  queryLength = writeString("q=", query, queryLength);
  queryLength = writeString(cityName, query, queryLength);
  queryLength = writeString("&units=metric&appid=", httpQuery, queryLength);
  queryLength = writeString(apiKey, query, queryLength);  

  queryLength = writeString(" HTTP/1.1\r\nHost: api.openweathermap.org\r\n", query, queryLength);
  queryLength = writeString("Connection: Closed\r\n\r\n", query, queryLength);
  
  return queryLength;
}

void sendCmd(char* cmd)
{
  Serial1.println(cmd);
}

void initLCD()
{
  sendCmd("Layer 0");
  sendCmd("Clear");
  //sendCmd("LoadFont \"/unbatang.ttf\"");

  sendCmd("DestroyLayer 1");
  sendCmd("DestroyLayer 2");
  sendCmd("DestroyLayer 3");
  sendCmd("DestroyLayer 4");
  sendCmd("DestroyLayer 5");
  sendCmd("DestroyLayer 6");
  sendCmd("DestroyLayer 7");
  sendCmd("DestroyLayer 8");
  sendCmd("DestroyLayer 9");
  sendCmd("DestroyLayer 10");
  sendCmd("DestroyLayer 11");
  sendCmd("DestroyLayer 12");
  sendCmd("DestroyLayer 13");

  createLayers();
  createPopup();

  showPopup("Loading...");

  sendCmd("DisableFlush");
  sendCmd("Layer 0");
  sendCmd("FontSize 48");  
  sendCmd("Image 0 0 \"/image/bk3.png\"");
  sendCmd("EnableFlush");
}

void createLayers()
{
  // weather condition
  sendCmd("CreateLayer 68 380 732 70 1");  
  // ICON
  sendCmd("CreateLayer 68 108 265 245 2");
  // City name
  sendCmd("CreateLayer 460 60 320 80 3");
  // Temperature
  sendCmd("CreateLayer 460 170 340 120 4");
  // Humidity
  sendCmd("CreateLayer 460 310 340 70 5");
}

void createPopup()
{  
  sendCmd("CreateLayer 80 180 640 120 6");
  sendCmd("Layer 6");
  sendCmd("DisableLayer 6");
}

void showPopup(String msg)
{
  String cmd;
  sendCmd("Layer 6");
  sendCmd("Clear");
  sendCmd("FontSize 72");
  sendCmd("Color FFFFFF");
  cmd = "Button 0 0 640 120 10 336699 336699 \"" + msg + "\"";
  sendCmd(cmd.c_str());
  sendCmd("EnableLayer 6");
}

void hidePopup()
{
  sendCmd("DisableLayer 6");
}

void printCity(String cityName)
{
  String cmd;
  sendCmd("Layer 3");
  sendCmd("DisableLayer 3");
  sendCmd("Clear");
  sendCmd("FontSize 60");
  sendCmd("Color FFFFFF");
  cmd = "FillText 0 60 \""; cmd = cmd + cityName + "\"";
  sendCmd(cmd.c_str());
}

void printTemperature(String temperature)
{
  String cmd;
  sendCmd("Layer 4");
  sendCmd("DisableLayer 4");
  sendCmd("Clear");
  sendCmd("FontSize 100");
  sendCmd("Color FFFFFF");
  cmd = "FillText 0 90 \""; cmd = cmd + temperature + "℃\"";
  sendCmd(cmd.c_str());
}

void printHumidity(String humidity)
{
  String cmd;
  sendCmd("Layer 5");
  sendCmd("DisableLayer 5");
  sendCmd("Clear");
  sendCmd("FontSize 48");
  sendCmd("Color FFFFFF");
  cmd = "FillText 0 50 \""; cmd = cmd + humidity + "%\"";
  sendCmd(cmd.c_str());
}

void printIcon(String id)
{
  sendCmd("Layer 2");
  sendCmd("DisableLayer 2");
  sendCmd("Clear");
  
  String cmd, icon;
  char code = id.charAt(0);
  switch(code)
  {
    case '2':
    case '3':
    case '5':
      icon = "/image/weather5.png";
      break;
    case '6':
      icon = "/image/weather7.png";
      break;
    case '7':
      icon = "/image/weather2.png";
      break;
     case '8':
      if(id.equals("800"))
        icon = "/image/weather1.png";
      else if(id.equals("801"))
        icon = "/image/weather4.png";
      else if(id.equals("802"))
        icon = "/image/weather2.png";
      else if(id.equals("803"))
        icon = "/image/weather3.png";
      else if(id.equals("804"))
        icon = "/image/weather3.png";
      break;
  }

  cmd = "Image 0 0 \"" + icon + "\"";
  sendCmd(cmd.c_str());
}

void printWeather(String weather)
{
  String cmd;
  sendCmd("Layer 1");
  sendCmd("DisableLayer 1");
  sendCmd("Clear");
  sendCmd("FontSize 48");
  sendCmd("Color FFFFFF");
  weather.toUpperCase();
  cmd = "FillText 0 50 \""; cmd = cmd + weather + "\"";
  //sendCmd(cmd.c_str());
}
