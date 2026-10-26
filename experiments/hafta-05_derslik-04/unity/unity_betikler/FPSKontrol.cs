// Basit birinci şahıs kontrolü (masaüstü test için; VR değil).
//   WASD / ok tuşları: yürü     Shift: koş        Space: zıpla
//   Fare: etrafa bak            F: uçma modu (çarpışmasız serbest gezinme; Q/E aşağı/yukarı)
//   Esc: imleci bırak, sol tık: imleci yeniden kilitle
// Eski Input Manager ve yeni Input System ile çalışır.
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

[RequireComponent(typeof(CharacterController))]
public class FPSKontrol : MonoBehaviour
{
    public float yurume = 1.6f;          // m/sn
    public float kosma = 3.5f;
    public float ucma = 4f;
    public float ziplama = 0.5f;         // zıplama yüksekliği, m
    public float yercekimi = 9.81f;
    public float fareHassasiyeti = 0.12f;
    public float gozYuksekligi = 1.6f;   // m

    CharacterController cc;
    Transform kam;
    float pitch, dikeyHiz;
    bool ucuyor;

    void Awake()
    {
        cc = GetComponent<CharacterController>();
        cc.height = 1.75f; cc.radius = 0.22f; cc.center = new Vector3(0, cc.height / 2f, 0);
        cc.stepOffset = 0.45f;            // 0,41 m'lik platforma basamaksız çıkılabilsin
        cc.slopeLimit = 50f; cc.skinWidth = 0.03f;
        var c = GetComponentInChildren<Camera>();
        if (c == null)
        {
            var eski = Camera.main;
            if (eski != null) eski.gameObject.SetActive(false);
            c = new GameObject("Kamera").AddComponent<Camera>();
            c.gameObject.AddComponent<AudioListener>();
            c.tag = "MainCamera";
            c.nearClipPlane = 0.05f;
        }
        kam = c.transform;
        kam.SetParent(transform, false);
        kam.localPosition = new Vector3(0, gozYuksekligi, 0);
        kam.localRotation = Quaternion.identity;
        Kilitle(true);
    }

    void Kilitle(bool k)
    {
        Cursor.lockState = k ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !k;
    }

    void Update()
    {
        Girdi(out Vector2 hareket, out Vector2 fare, out bool kos, out bool zipla, out bool ucmaTusu,
              out float yukari, out bool esc, out bool tik);
        if (esc) Kilitle(false);
        if (tik) Kilitle(true);
        if (ucmaTusu) { ucuyor = !ucuyor; cc.enabled = !ucuyor; dikeyHiz = 0; }

        if (Cursor.lockState == CursorLockMode.Locked)
        {
            transform.Rotate(0, fare.x * fareHassasiyeti, 0);
            pitch = Mathf.Clamp(pitch - fare.y * fareHassasiyeti, -85f, 85f);
            kam.localRotation = Quaternion.Euler(pitch, 0, 0);
        }

        if (ucuyor)
        {
            var yon = kam.forward * hareket.y + kam.right * hareket.x + Vector3.up * yukari;
            transform.position += yon * (kos ? ucma * 2f : ucma) * Time.deltaTime;
            return;
        }
        var duz = (transform.forward * hareket.y + transform.right * hareket.x);
        if (duz.sqrMagnitude > 1f) duz.Normalize();
        var v = duz * (kos ? kosma : yurume);
        if (cc.isGrounded)
        {
            dikeyHiz = -1f;
            if (zipla) dikeyHiz = Mathf.Sqrt(2f * yercekimi * ziplama);
        }
        dikeyHiz -= yercekimi * Time.deltaTime;
        v.y = dikeyHiz;
        cc.Move(v * Time.deltaTime);
        if (transform.position.y < -5f) transform.position = new Vector3(transform.position.x, 1f, transform.position.z);
    }

    static void Girdi(out Vector2 h, out Vector2 fare, out bool kos, out bool zipla, out bool ucmaTusu,
                      out float yukari, out bool esc, out bool tik)
    {
#if ENABLE_INPUT_SYSTEM
        var k = Keyboard.current; var m = Mouse.current;
        h = Vector2.zero; fare = Vector2.zero; kos = zipla = ucmaTusu = esc = tik = false; yukari = 0;
        if (k != null)
        {
            h.x = (k.dKey.isPressed || k.rightArrowKey.isPressed ? 1 : 0) - (k.aKey.isPressed || k.leftArrowKey.isPressed ? 1 : 0);
            h.y = (k.wKey.isPressed || k.upArrowKey.isPressed ? 1 : 0) - (k.sKey.isPressed || k.downArrowKey.isPressed ? 1 : 0);
            kos = k.leftShiftKey.isPressed; zipla = k.spaceKey.wasPressedThisFrame;
            ucmaTusu = k.fKey.wasPressedThisFrame; esc = k.escapeKey.wasPressedThisFrame;
            yukari = (k.eKey.isPressed ? 1 : 0) - (k.qKey.isPressed ? 1 : 0);
        }
        if (m != null) { fare = m.delta.ReadValue(); tik = m.leftButton.wasPressedThisFrame; }
#else
        h = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        fare = new Vector2(Input.GetAxisRaw("Mouse X"), Input.GetAxisRaw("Mouse Y")) * 10f;
        kos = Input.GetKey(KeyCode.LeftShift); zipla = Input.GetKeyDown(KeyCode.Space);
        ucmaTusu = Input.GetKeyDown(KeyCode.F); esc = Input.GetKeyDown(KeyCode.Escape);
        tik = Input.GetMouseButtonDown(0);
        yukari = (Input.GetKey(KeyCode.E) ? 1 : 0) - (Input.GetKey(KeyCode.Q) ? 1 : 0);
#endif
    }
}
