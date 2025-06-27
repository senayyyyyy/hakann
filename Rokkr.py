<?php

function fetchRedirectUrl($url) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_HEADER => true,
        CURLOPT_NOBODY => true,
        CURLOPT_USERAGENT => $_SERVER['HTTP_USER_AGENT']
    ]);
    $response = curl_exec($ch);
    curl_close($ch);

    if (preg_match('/Location:\s*(.+)/i', $response, $matches)) {
        return trim($matches[1]);
    }

    return false;
}

function fetchContent($url) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_USERAGENT => $_SERVER['HTTP_USER_AGENT'],
        CURLOPT_HTTPHEADER => ['Referer: https://vavoo.to/']
    ]);
    $data = curl_exec($ch);
    $contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return [$data, $contentType, $httpCode];
}

// .ts segment isteği
if (isset($_GET['ts'])) {
    $tsUrl = base64_decode($_GET['ts']);
    if (!filter_var($tsUrl, FILTER_VALIDATE_URL)) {
        http_response_code(400);
        exit("Geçersiz TS URL");
    }
    [$data, $type, $code] = fetchContent($tsUrl);
    http_response_code($code);
    header("Content-Type: $type");
    echo $data;
    exit;
}

// m3u8 isteği
if (!isset($_GET['id'])) {
    http_response_code(400);
    exit("ID eksik");
}

$id = preg_replace('/[^a-zA-Z0-9]/', '', $_GET['id']);
$entry = "https://vavoo.to/vavoo-iptv/play/" . $id;

$realM3u8 = fetchRedirectUrl($entry);
if (!$realM3u8) {
    http_response_code(500);
    exit("Gerçek m3u8 linki alınamadı");
}

// M3U8 içeriğini al
[$m3u8, $type, $code] = fetchContent($realM3u8);
if ($code !== 200 || empty($m3u8)) {
    http_response_code(500);
    exit("M3U8 dosyası alınamadı");
}

// .ts segmentleri base64 ile proxy'le
$base = dirname($realM3u8) . '/';
$proxied = preg_replace_callback('/^(.+\.ts)$/m', function($m) use ($base) {
    $tsUrl = $base . $m[1];
    $encoded = urlencode(base64_encode($tsUrl));
    return "https://kendi domeninizi ekleyin/Rokkr.php?ts=$encoded";
}, $m3u8);

// Header ve çıktı
header("Content-Type: application/vnd.apple.mpegurl");
echo $proxied;