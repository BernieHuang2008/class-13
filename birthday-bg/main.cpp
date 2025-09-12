#include <windows.h>
#include <gdiplus.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <map>
#include <sstream>
#include <ctime>
#include <algorithm>
#include <memory>

#define RYML_SINGLE_HDR_DEFINE_NOW
#include "rapidyaml-0.9.0.hpp"

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "advapi32.lib")

using namespace Gdiplus;
using namespace std;

#define DEBUG
#ifdef DEBUG
#include <stdio.h>
#define log printf
#else
#define log(x)
#endif

// Structure to hold person data
struct Person {
    string name;
    string birthday;
    string other_info;
};

// Structure to hold font configuration
struct FontConfig {
    int size;
    string family;
    string color;
    
    FontConfig() : size(24), family("Arial"), color("ffffff") {}
};

// Structure to hold render configuration
struct RenderConfig {
    int x, y;
    string info;
    FontConfig font;
};

// Structure to hold all configuration
struct Config {
    vector<RenderConfig> render;
};

// Unified file reading function
vector<char> read_file_as_bin(const string& filename) {
    ifstream file(filename, ios::binary | ios::ate);
    if (!file.is_open()) {
        return vector<char>();
    }
    
    streamsize size = file.tellg();
    file.seekg(0, ios::beg);
    
    vector<char> buffer(size);
    if (!file.read(buffer.data(), size)) {
        return vector<char>();
    }
    
    return buffer;
}

// Parse CSV file
vector<Person> parse_csv(const string& filename) {
    vector<Person> people;
    vector<char> data = read_file_as_bin(filename);
    if (data.empty()) return people;
    
    string content(data.begin(), data.end());
    istringstream stream(content);
    string line;
    
    // Skip header line
    if (getline(stream, line)) {
        while (getline(stream, line)) {
            if (line.empty()) continue;
            
            Person person;
            istringstream lineStream(line);
            string field;
            
            // Parse name
            if (getline(lineStream, field, ',')) {
                person.name = field;
                // Trim whitespace
                person.name.erase(0, person.name.find_first_not_of(" \t"));
                person.name.erase(person.name.find_last_not_of(" \t") + 1);
            }
            
            // Parse birthday
            if (getline(lineStream, field, ',')) {
                person.birthday = field;
                person.birthday.erase(0, person.birthday.find_first_not_of(" \t"));
                person.birthday.erase(person.birthday.find_last_not_of(" \t") + 1);
            }
            
            // Parse other_info
            if (getline(lineStream, field)) {
                person.other_info = field;
                person.other_info.erase(0, person.other_info.find_first_not_of(" \t"));
                person.other_info.erase(person.other_info.find_last_not_of(" \t") + 1);
            }
            
            people.push_back(person);
        }
    }
    
    return people;
}

// Simple YAML parser using rapidyaml
Config parse_yaml(const string& filename) {
    Config config;
    vector<char> data = read_file_as_bin(filename);
    if (data.empty()) return config;
    
    try {
        // Parse YAML using rapidyaml
        ryml::csubstr yaml_data(data.data(), data.size());
        ryml::Tree tree = ryml::parse_in_arena(yaml_data);
        ryml::NodeRef root = tree.rootref();
        
        // Check if render node exists
        if (root.has_child("render")) {
            ryml::NodeRef render_node = root["render"];
            
            // Iterate through render items
            for (ryml::NodeRef item : render_node.children()) {
                RenderConfig render_config;
                
                // Parse position
                if (item.has_child("pos")) {
                    ryml::NodeRef pos = item["pos"];
                    if (pos.has_child("x")) {
                        pos["x"] >> render_config.x;
                    }
                    if (pos.has_child("y")) {
                        pos["y"] >> render_config.y;
                    }
                }
                
                // Parse info field
                if (item.has_child("info")) {
                    string info_str;
                    item["info"] >> info_str;
                    render_config.info = info_str;
                }
                
                // Parse font configuration
                if (item.has_child("font")) {
                    ryml::NodeRef font = item["font"];
                    
                    if (font.has_child("size")) {
                        font["size"] >> render_config.font.size;
                    }
                    
                    if (font.has_child("family")) {
                        string family_str;
                        font["family"] >> family_str;
                        render_config.font.family = family_str;
                    }
                    
                    if (font.has_child("color")) {
                        string color_str;
                        font["color"] >> color_str;
                        render_config.font.color = color_str;
                    }
                }
                
                config.render.push_back(render_config);
            }
        }
    }
    catch (const std::exception& e) {
        log("YAML parsing error: %s\n", e.what());
    }
    
    return config;
}

// Get current date in M.D format
string get_current_date() {
    time_t now = time(0);
    tm* ltm = localtime(&now);
    
    int month = 1 + ltm->tm_mon;
    int day = ltm->tm_mday;
    
    return to_string(month) + "." + to_string(day);
}

// Find people with birthday today
vector<Person> find_birthday_people(const vector<Person>& people) {
    vector<Person> birthday_people;
    string today = get_current_date();
    
    for (const auto& person : people) {
        if (person.birthday == today) {
            birthday_people.push_back(person);
        }
    }
    
    return birthday_people;
}

// Get field value from person
string get_person_field(const Person& person, const string& field) {
    if (field == "name") return person.name;
    if (field == "birthday") return person.birthday;
    if (field == "other_info") return person.other_info;
    return "";
}

// Convert hex color string to GDI+ Color
Color hex_to_color(const string& hex) {
    string color_str = hex;
    if (color_str.length() == 6) {
        unsigned int r, g, b;
        sscanf(color_str.substr(0, 2).c_str(), "%x", &r);
        sscanf(color_str.substr(2, 2).c_str(), "%x", &g);
        sscanf(color_str.substr(4, 2).c_str(), "%x", &b);
        return Color(255, r, g, b);
    }
    return Color(255, 255, 255, 255); // Default to white
}

// Create font from TTF file path
unique_ptr<Font> create_font_from_file(const string& font_path, int size) {
    // Convert to wide string
    wstring wfont_path(font_path.begin(), font_path.end());
    
    // Create private font collection
    PrivateFontCollection fontCollection;
    Status status = fontCollection.AddFontFile(wfont_path.c_str());
    
    if (status == Ok && fontCollection.GetFamilyCount() > 0) {
        FontFamily* families = new FontFamily[1];
        int found = 0;
        fontCollection.GetFamilies(1, families, &found);
        
        if (found > 0) {
            unique_ptr<Font> font(new Font(&families[0], static_cast<REAL>(size), FontStyleRegular, UnitPixel));
            delete[] families;
            return font;
        }
        delete[] families;
    }
    
    // Fallback to system font
    FontFamily fontFamily(L"Arial");
    return unique_ptr<Font>(new Font(&fontFamily, static_cast<REAL>(size), FontStyleRegular, UnitPixel));
}

// Render text on image
bool render_image(const string& template_path, const string& output_path,
                 const vector<Person>& birthday_people, const Config& config) {
    
    // Initialize GDI+
    GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    if (GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL) != Ok) {
        return false;
    }
    
    // Load template image
    wstring wtemplate_path(template_path.begin(), template_path.end());
    unique_ptr<Bitmap> bitmap(new Bitmap(wtemplate_path.c_str()));
    if (bitmap->GetLastStatus() != Ok) {
        GdiplusShutdown(gdiplusToken);
        return false;
    }
    
    // Create graphics object
    unique_ptr<Graphics> graphics(new Graphics(bitmap.get()));
    if (graphics->GetLastStatus() != Ok) {
        GdiplusShutdown(gdiplusToken);
        return false;
    }
    
    // Set text rendering quality
    graphics->SetTextRenderingHint(TextRenderingHintAntiAlias);
    
    // Render text for each birthday person
    for (const auto& person : birthday_people) {
        for (const auto& render : config.render) {
            string text = get_person_field(person, render.info);
            wstring wtext(text.begin(), text.end());
            
            // Create font from configuration
            unique_ptr<Font> font = create_font_from_file(render.font.family, render.font.size);
            
            // Create brush with configured color
            Color textColor = hex_to_color(render.font.color);
            SolidBrush brush(textColor);
            
            // Render text at specified position
            PointF point(static_cast<REAL>(render.x), static_cast<REAL>(render.y));
            graphics->DrawString(wtext.c_str(), -1, font.get(), point, &brush);
        }
    }
    
    // Save the image
    CLSID pngClsid;
    CLSIDFromString(L"{557CF406-1A04-11D3-9A73-0000F81EF32E}", &pngClsid);
    
    wstring woutput_path(output_path.begin(), output_path.end());
    Status status = bitmap->Save(woutput_path.c_str(), &pngClsid, NULL);
    
    GdiplusShutdown(gdiplusToken);
    return status == Ok;
}

// Set desktop wallpaper using Windows API
bool set_desktop_wallpaper(const string& image_path) {
    wstring wimage_path(image_path.begin(), image_path.end());
    
    // Set wallpaper
    BOOL result = SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        (PVOID)wimage_path.c_str(),
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    );
    
    if (result) {
        // Set wallpaper style to fit/fill
        HKEY hKey;
        if (RegOpenKeyExW(HKEY_CURRENT_USER, 
                         L"Control Panel\\Desktop", 
                         0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
            
            // Set wallpaper style (2 = stretch, 6 = fit, 10 = fill)
            const wchar_t* wallpaperStyle = L"10"; // Fill
            RegSetValueExW(hKey, L"WallpaperStyle", 0, REG_SZ, 
                          (const BYTE*)wallpaperStyle, 
                          (wcslen(wallpaperStyle) + 1) * sizeof(wchar_t));
            
            // Set tile wallpaper (0 = no tile)
            const wchar_t* tileWallpaper = L"0";
            RegSetValueExW(hKey, L"TileWallpaper", 0, REG_SZ, 
                          (const BYTE*)tileWallpaper, 
                          (wcslen(tileWallpaper) + 1) * sizeof(wchar_t));
            
            RegCloseKey(hKey);
        }
        
        // Refresh desktop
        SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, 
                             (PVOID)wimage_path.c_str(), 
                             SPIF_UPDATEINIFILE | SPIF_SENDCHANGE);
    }
    
    return result != FALSE;
}

// Main function - no console window
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, 
                   LPSTR lpCmdLine, int nCmdShow) {
#ifdef DEBUG
    freopen("log.txt", "w", stdout);
#endif
    log("Program started.\n");
    
    // Parse CSV data
    vector<Person> people = parse_csv("data.csv");
    if (people.empty()) {
        log("No data found in CSV.\n");
        return 1;
    }
    log("Loaded %zu people from CSV.\n", people.size());
    
    // Parse config
    Config config = parse_yaml("config.yaml");
    if (config.render.empty()) {
        log("No render configuration found in YAML.\n");
        return 1;
    }
    log("Loaded %zu render configurations from YAML.\n", config.render.size());
    
    // Find birthday people
    vector<Person> birthday_people = find_birthday_people(people);
    
    string wallpaper_path;
    
    if (birthday_people.empty()) {
        // No birthdays today, use default wallpaper
        log("No birthdays today.\n");
        wallpaper_path = "bgs\\default.png";
    } else {
        log("Found %zu birthday(s) today.\n", birthday_people.size());
        // Render birthday wallpaper
        string output_path = "bgs\\birthday_rendered.png";
        if (render_image("bgs\\template.png", output_path, birthday_people, config)) {
            wallpaper_path = output_path;
        } else {
            // Fallback to default if rendering fails
            wallpaper_path = "bgs\\default.png";
        }
    }
    
    // Convert to absolute path
    char full_path[MAX_PATH];
    if (GetFullPathNameA(wallpaper_path.c_str(), MAX_PATH, full_path, NULL)) {
        wallpaper_path = full_path;
    }
    
    // Set desktop wallpaper
    set_desktop_wallpaper(wallpaper_path);
    
    return 0;
}