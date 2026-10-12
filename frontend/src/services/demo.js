export function getPublicDemoUrl(configuredUrl, currentOrigin) {
  try {
    const url = new URL(configuredUrl || '');
    if (url.protocol !== 'https:' || url.username || url.password || url.origin === currentOrigin) return '';
    return url.href;
  } catch {
    return '';
  }
}
