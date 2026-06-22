const repository = "altibo/SimplyAbrechnung";
const requiredAssets = {
  windows: "SimplyAbrechnung-Windows-Setup.exe",
  mac: "SimplyAbrechnung-macOS.pkg",
};

const formatSize = (bytes) => `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB`;

const applyRelease = (release) => {
  const assets = new Map(release.assets.map((asset) => [asset.name, asset]));
  const windows = assets.get(requiredAssets.windows);
  const mac = assets.get(requiredAssets.mac);
  if (!windows || !mac) return false;

  const versionMatch = release.tag_name.match(/^v([^\-]+)(?:-|$)/);
  const version = versionMatch ? versionMatch[1] : release.tag_name.replace(/^v/, "");
  const date = new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
    .format(new Date(release.published_at));

  document.querySelector("#version-label").textContent = `Version ${version}`;
  document.querySelector("#release-meta").textContent = `${release.name} · veröffentlicht am ${date}`;
  document.querySelector("#release-link").href = release.html_url;
  document.querySelector("#windows-download").href = windows.browser_download_url;
  document.querySelector("#mac-download").href = mac.browser_download_url;
  document.querySelector("#windows-meta").textContent = `Setup · ${formatSize(windows.size)} · Windows 10/11`;
  document.querySelector("#mac-meta").textContent = `Installationspaket · ${formatSize(mac.size)}`;
  return true;
};

fetch(`https://api.github.com/repos/${repository}/releases?per_page=10`, {
  headers: { Accept: "application/vnd.github+json" },
})
  .then((response) => {
    if (!response.ok) throw new Error(`GitHub API: ${response.status}`);
    return response.json();
  })
  .then((releases) => releases.find((release) => !release.draft && applyRelease(release)))
  .catch(() => {
    // Die statischen Angaben und Links im HTML bleiben als belastbarer Fallback erhalten.
  });
