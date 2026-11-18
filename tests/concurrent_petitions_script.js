(async () => {
  const paths = [
    "/books",
    "/authors",
    "/borrowers",
    "/loans/active",
    "/books/available",
  ];

  async function sha256Hex(bytes) {
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(hash), byte =>
      byte.toString(16).padStart(2, "0")
    ).join("");
  }

  const emptyBodyDigest = await sha256Hex(new Uint8Array());
  const startedAt = performance.now();

  const results = await Promise.allSettled(
    paths.map(async path => {
      const requestStartedAt = performance.now();
      const response = await fetch(`${location.origin}${path}?demo=${Date.now()}`, {
        method: "GET",
        headers: { "X-Content-Digest": emptyBodyDigest },
        cache: "no-store",
      });

      const body = new Uint8Array(await response.arrayBuffer());
      const expectedDigest = await sha256Hex(body);
      const receivedDigest = response.headers.get("X-Content-Digest");

      return {
        path,
        status: response.status,
        ms: +(performance.now() - requestStartedAt).toFixed(1),
        digestOK: receivedDigest?.trim().toLowerCase() === expectedDigest,
      };
    })
  );

  console.table(results.map((result, index) =>
    result.status === "fulfilled"
      ? result.value
      : { path: paths[index], error: String(result.reason) }
  ));

  console.log(
    `Lanzadas ${paths.length} peticiones concurrentes; ` +
    `${(performance.now() - startedAt).toFixed(1)} ms en total.`
  );
})();