(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const internalLinks = document.querySelectorAll('a[href^="#"]');

  internalLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
      window.history.replaceState(null, "", link.getAttribute("href"));
    });
  });

  if (!window.gsap || !window.ScrollTrigger) return;

  gsap.registerPlugin(ScrollTrigger);
  gsap.defaults({ overwrite: "auto" });

  const desktop = window.matchMedia("(min-width: 681px)").matches;
  const travel = reduceMotion ? 12 : desktop ? 38 : 24;
  const duration = reduceMotion ? 0.42 : 0.82;
  const introOverlap = reduceMotion ? "-=0.16" : "-=0.42";

  gsap.timeline({ defaults: { duration, ease: "power3.out" } })
    .fromTo(".brand", { autoAlpha: 0, y: -18 }, { autoAlpha: 1, y: 0 })
    .fromTo(
      "[data-intro-group] > *",
      { autoAlpha: 0, y: travel },
      { autoAlpha: 1, y: 0, stagger: reduceMotion ? 0.055 : 0.11 },
      introOverlap
    );

  gsap.utils.toArray("[data-reveal]").forEach((element) => {
    gsap.fromTo(
      element,
      { autoAlpha: 0, y: travel },
      {
        autoAlpha: 1,
        y: 0,
        duration: reduceMotion ? 0.4 : 0.78,
        ease: "power3.out",
        scrollTrigger: {
          trigger: element,
          start: "top 88%",
          end: "bottom 14%",
          toggleActions: "play none none reverse"
        }
      }
    );
  });

  gsap.fromTo(
    "[data-reveal-group] > *",
    { autoAlpha: 0, y: travel },
    {
      autoAlpha: 1,
      y: 0,
      duration: reduceMotion ? 0.38 : 0.72,
      stagger: reduceMotion ? 0.04 : 0.08,
      ease: "power3.out",
      scrollTrigger: {
        trigger: "[data-reveal-group]",
        start: "top 84%",
        end: "bottom 12%",
        toggleActions: "play none none reverse"
      }
    }
  );

  gsap.utils.toArray("[data-section]").forEach((section) => {
    gsap.fromTo(
      section,
      { backgroundPositionY: "14px" },
      {
        backgroundPositionY: "0px",
        ease: "none",
        scrollTrigger: {
          trigger: section,
          start: "top bottom",
          end: "bottom top",
          scrub: 0.8
        }
      }
    );
  });

  gsap.utils.toArray(".module-card").forEach((card, index) => {
    gsap.fromTo(
      card,
      { y: 18, rotateX: 2, transformPerspective: 900 },
      {
        y: 0,
        rotateX: 0,
        ease: "power2.out",
        scrollTrigger: {
          trigger: card,
          start: "top 96%",
          end: "top 66%",
          scrub: reduceMotion ? false : 0.55,
          invalidateOnRefresh: true
        },
        delay: reduceMotion ? 0 : index * 0.02
      }
    );
  });

  if (!reduceMotion) {
    gsap.to('[data-parallax="hero"]', {
      yPercent: 8,
      scale: 1.035,
      ease: "none",
      scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: 0.6 }
    });

    gsap.fromTo(
      '[data-parallax="closing"]',
      { yPercent: -5, scale: 1.04 },
      {
        yPercent: 5,
        ease: "none",
        scrollTrigger: { trigger: ".closing", start: "top bottom", end: "bottom top", scrub: 0.65 }
      }
    );
  }

  gsap.to(".scroll-progress span", {
    scaleX: 1,
    ease: "none",
    scrollTrigger: { start: 0, end: "max", scrub: 0.15 }
  });

  window.addEventListener("load", () => ScrollTrigger.refresh(), { once: true });
})();
