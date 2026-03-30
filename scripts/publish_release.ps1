param(
  [Parameter(Mandatory=$true)][string]$Version,
  [Parameter(Mandatory=$true)][string]$ArtifactDir
)

$ErrorActionPreference = "Stop"

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
  throw "Version must be semantic format like 1.0.0"
}

$tag = "v$Version"

if (git rev-parse --verify --quiet $tag) {
  throw "Tag '$tag' already exists."
}

git tag -a $tag -m "Release $tag"
git push origin $tag

$artifactPath = Resolve-Path $ArtifactDir
$checksumsPath = Join-Path $artifactPath "checksums.txt"
Get-ChildItem -Path $artifactPath -File | ForEach-Object {
  $hash = Get-FileHash -Algorithm SHA256 -Path $_.FullName
  "{0}  {1}" -f $hash.Hash.ToLower(), $_.Name
} | Set-Content -LiteralPath $checksumsPath

$artifactFiles = Get-ChildItem -Path $artifactPath -File | ForEach-Object { $_.FullName }
gh release create $tag --title "Arena Companion $tag" --notes-file docs/release-notes.md @artifactFiles
