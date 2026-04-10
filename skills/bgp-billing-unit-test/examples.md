# BGP Billing 测试示例

本文档提供各层测试的完整示例。

## 1. Service 层测试示例

### 1.1 基础 Service 测试

```java
@DisplayName("PaymentGoogleService 单元测试")
class PaymentGoogleServiceTest extends BaseUnitTest {

    @Mock
    private PaymentGoogleRepository paymentGoogleRepository;

    @Mock
    private TrackerUtil trackerUtil;

    @InjectMocks
    private PaymentGoogleService paymentGoogleService;

    private PaymentGoogle testPayment;

    @BeforeEach
    void setUp() {
        testPayment = TestDataFactory.createGooglePayment();
    }

    @Nested
    @DisplayName("getByOrderId 方法")
    class GetByOrderId {

        @Test
        @DisplayName("当 orderId 存在时,应返回对应的支付记录")
        void returnsPayment_whenOrderIdExists() {
            // Given
            String orderId = testPayment.getTransactionId();
            when(paymentGoogleRepository.findByTransactionId(orderId))
                .thenReturn(Mono.just(testPayment));

            // When & Then
            StepVerifier.create(paymentGoogleService.getByOrderId(orderId))
                .assertNext(payment -> {
                    assertThat(payment.getTransactionId()).isEqualTo(orderId);
                })
                .verifyComplete();
        }

        @Test
        @DisplayName("当 orderId 为空时,应抛出参数异常")
        void throwsException_whenOrderIdIsEmpty() {
            // When & Then
            StepVerifier.create(paymentGoogleService.getByOrderId(""))
                .expectError(IllegalArgumentException.class)
                .verify();
        }

        @Test
        @DisplayName("当 orderId 不存在时,应返回空")
        void returnsEmpty_whenOrderIdNotExists() {
            // Given
            when(paymentGoogleRepository.findByTransactionId("non-existent"))
                .thenReturn(Mono.empty());

            // When & Then
            StepVerifier.create(paymentGoogleService.getByOrderId("non-existent"))
                .verifyComplete();
        }
    }

    @Nested
    @DisplayName("save 方法")
    class Save {

        @Test
        @DisplayName("当支付记录有效时,应保存成功")
        void savesSuccessfully_whenPaymentIsValid() {
            // Given
            when(paymentGoogleRepository.save(testPayment))
                .thenReturn(Mono.just(testPayment));

            // When & Then
            StepVerifier.create(paymentGoogleService.save(testPayment))
                .assertNext(saved -> {
                    assertThat(saved.getId()).isEqualTo(testPayment.getId());
                })
                .verifyComplete();
        }
    }
}
```

### 1.2 带参数校验的 Service 测试

```java
@DisplayName("GoogleValidateService 单元测试")
class GoogleValidateServiceTest extends BaseUnitTest {

    @Mock
    private GoogleValidateRpc googleValidateRpc;

    @Mock
    private PaymentGoogleService paymentGoogleService;

    @InjectMocks
    private GoogleValidateService googleValidateService;

    @Nested
    @DisplayName("checkValidateParams 参数校验测试")
    class CheckValidateParamsTests {

        @Test
        @DisplayName("当 receipt 为空时,应抛出参数异常")
        void throwsException_whenReceiptIsBlank() {
            BillingInfoDto dto = new BillingInfoDto();
            dto.setReceipt("");

            assertThatThrownBy(() -> googleValidateService.checkValidateParams(dto))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("receipt is blank");
        }
    }

    @Nested
    @DisplayName("fillPaymentByRpcResult RPC 结果处理测试")
    class FillPaymentByRpcResultTests {

        @Test
        @DisplayName("当 purchaseType 为 TEST 时,应设置环境为 SANDBOX")
        void shouldSetSandboxEnv_whenPurchaseTypeIsTest() {
            ProductPurchase rpcResult = new ProductPurchase();
            rpcResult.setPurchaseType(GoogleValidateRpcConstant.PurchaseType.TEST);
            rpcResult.setOrderId("GPA.1234");
            rpcResult.setPurchaseTimeMillis(System.currentTimeMillis());

            PaymentGoogle payment = new PaymentGoogle();

            StepVerifier.create(
                googleValidateService.fillPaymentByRpcResult(dto, appInfo, rpcResult, payment)
                    .contextWrite(ctx -> StoreUtil.set(ctx, "payload", payload))
            )
            .assertNext(result -> {
                assertThat(result.getEnv()).isEqualTo(PaymentConstant.Env.SANDBOX);
            })
            .verifyComplete();
        }
    }
}
```

## 2. Controller 层测试示例

```java
@DisplayName("VerifyController 集成测试")
class VerifyControllerIntegrationTest extends BaseIntegrationTest {

    @BeforeEach
    void setUp() {
        // 使用 reset() 重置 Mock 状态,确保测试隔离
        reset(appleValidateService, googleValidateService, appProperties);
        testAppInfo = TestDataFactory.createAppInfo();
        when(appProperties.getApp(anyInt())).thenReturn(testAppInfo);
        when(appProperties.getAppOrNull(anyInt())).thenReturn(testAppInfo);
    }

    @Nested
    @DisplayName("verify 方法")
    class Verify {
        @Test
        @DisplayName("当 Apple 支付验证请求有效时,应返回验证结果")
        void returnsValidateResult_whenValidAppleRequest() {
            // Given
            ValidateDto request = TestDataFactory.createValidateDto(Constant.Channel.IOS);
            ValidateRespDto expectedResponse = TestDataFactory.createValidateRespDto(Constant.Channel.IOS);
            when(appleValidateService.validate(any(), any(), any()))
                    .thenReturn(CompletableFuture.completedFuture(expectedResponse));

            // When & Then - 使用 TestRequestHelper,不需要传递 appId 和 sign
            // 注意:使用完整路径
            String path = "/billing/payment/verify";
            MTResponse<ValidateRespDto> mtResponse = TestRequestHelper.postToServerWithJsonForOK(
                    path, request, Map.of(), ValidateRespDto.class);
            ValidateRespDto data = mtResponse.getData();

            assertThat(data.getChannel()).isEqualTo(Constant.Channel.IOS);
            verify(appleValidateService).validate(any(), any(), any());
        }

        @Test
        @DisplayName("当返回 List 时,需要手动解析响应")
        void returnsList_whenRequestValid() {
            // Given
            when(service.getList(any())).thenReturn(Flux.just("item1", "item2"));

            // When & Then
            String path = "/billing/payment/finish";
            String responseBody = TestRequestHelper.postToServerWithJsonForOK(
                    path, request, Map.of(), String.class);

            // 手动解析 List 响应
            MTResponse<List<String>> mtResponse = JsonUtil.parse(response, MTResponse.class, List.class);
            List<String> data = mtResponse.getData();
            assertThat(result).hasSize(2);
        }
    }
}
```

## 3. Filter 层测试示例

```java
@DisplayName("AppCheckFilter 集成测试")
class AppCheckFilterIntegrationTest extends BaseIntegrationTest {

    @BeforeEach
    void setUp() {
        reset(appProperties);
        testAppInfo = TestDataFactory.createAppInfo();
        when(appProperties.getApp(anyInt())).thenReturn(testAppInfo);
        when(appProperties.getAppOrNull(anyInt())).thenReturn(testAppInfo);
    }

    @Nested
    @DisplayName("路径跳过逻辑")
    class PathSkipLogic {

        @Test
        @DisplayName("当路径不包含 /billing 时,应跳过 Filter")
        void skipsFilter_whenPathNotContainsBilling() {
            // Given - 使用不包含 /billing 的路径
            String path = "/api/other";

            // When & Then - Filter 应被跳过,不会校验 appId
            TestRequestHelper.postToServerWithJsonForOK(
                    path, request, Map.of(), String.class);

            // 验证 AppProperties 未被调用(因为 Filter 被跳过)
            verify(appProperties, never()).getApp(anyInt());
        }
    }

    @Nested
    @DisplayName("appId header 校验")
    class AppIdHeaderValidation {

        @Test
        @DisplayName("当 appId header 为空时,应返回 403 错误")
        void returns403_whenAppIdHeaderIsEmpty() {
            // Given - 通过自定义 headers 覆盖默认行为,设置空的 appId
            Map<String, String> customHeaders = Map.of("appId", "");

            // When & Then - 应返回 403 错误
            TestRequestHelper.postToServerWithJsonForError(
                    "/billing/payment/verify", request, customHeaders, 403);
        }

        @Test
        @DisplayName("当 appId header 有效时,应通过校验")
        void passesValidation_whenAppIdHeaderIsValid() {
            // Given - 使用默认的 TestRequestHelper 行为(自动添加有效的 appId)

            // When & Then - 应通过校验
            TestRequestHelper.postToServerWithJsonForOK(
                    "/billing/payment/verify", request, Map.of(), String.class);

            // 验证 AppProperties 被调用
            verify(appProperties).getApp(anyInt());
        }
    }
}
```

## 4. SQS 消息处理器测试示例

```java
@DisplayName("TrackMessageHandler 单元测试")
class TrackMessageHandlerTest extends BaseUnitTest {

    @Mock
    private ApplicationContext applicationContext;

    @Mock
    private TrackerUtil trackerUtil;

    @Mock
    private AbstractSqsMessageChannelProcessor<Payment> processor;

    @InjectMocks
    private TrackMessageHandler handler;

    @Test
    @DisplayName("当消息有效时,应成功处理并发送埋点")
    void shouldProcessMessage_whenMessageIsValid() {
        TrackSqsMsgDto msg = createTestMessage();
        PaymentGoogle payment = createTestPayment();

        when(applicationContext.getBean(anyString(), eq(AbstractSqsMessageChannelProcessor.class)))
            .thenReturn(processor);
        when(processor.getPayment(anyString(), anyString()))
            .thenReturn(Mono.just(payment));
        when(processor.buildTrackInfo(any(), any()))
            .thenReturn(Mono.just(msg.getTrackInfo()));
        when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
            .thenReturn(Mono.empty());
        when(processor.updatePayment(any(), anyString()))
            .thenReturn(Mono.just(1));

        // 不应抛出异常
        assertThatCode(() -> handler.handle(msg)).doesNotThrowAnyException();

        verify(trackerUtil).sendTrack(anyString(), anyInt(), anyString());
    }

    @Test
    @DisplayName("当解码消息为空时,应记录错误日志")
    void shouldLogError_whenMessageIsBlank() {
        TrackSqsMsgDto result = handler.decode("");
        assertThat(result).isNull();
    }
}
```

## 5. Util 工具类测试示例

```java
@DisplayName("TrackerUtil 单元测试")
class TrackerUtilTest extends BaseUnitTest {

    @Test
    @DisplayName("应正确构建 Google 退款埋点信息")
    void shouldBuildGoogleRefundTrackInfo() {
        PaymentGoogle payment = new PaymentGoogle();
        payment.setApp(1203);
        payment.setDeviceId("device-123");
        payment.setUserId("user-456");
        payment.setTransactionId("GPA.1234");
        payment.setProductId("com.example.product");
        payment.setRefundReason("0:UserRequest");
        payment.setPaymentTime(1609459200);
        payment.setRefundAt(1609545600);
        payment.setUsdPrice("9.99");
        payment.setCurrency("USD");
        payment.setPrice("9.99");

        Map<String, Object> result = TrackerUtil.buildGoogleRefundTrackInfo(payment);

        assertThat(result)
            .containsEntry("app", 1203)
            .containsEntry("$client", "Android")
            .containsEntry("$uid", "device-123")
            .containsEntry("$inapp_id", "user-456");

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> events = (List<Map<String, Object>>) result.get("$events");
        assertThat(events).hasSize(1);
        assertThat(events.get(0))
            .containsEntry("$action", "$refund")
            .containsEntry("v1", "GPA.1234")
            .containsEntry("v2", "com.example.product");
    }
}
```

## 6. 参数化测试示例

```java
@DisplayName("参数化测试示例")
class ParameterizedTestExamples extends BaseUnitTest {

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "  "})
    @DisplayName("当 orderId 为空白字符串时,应抛出异常")
    void shouldThrowException_whenOrderIdIsBlank(String orderId) {
        StepVerifier.create(paymentGoogleService.getByOrderId(orderId))
            .expectError(IllegalArgumentException.class)
            .verify();
    }

    @ParameterizedTest
    @CsvSource({
        "iOS, APPLE_VALIDATE_SERVICE",
        "google, GOOGLE_VALIDATE_SERVICE",
        "amazon, AMAZON_VALIDATE_SERVICE"
    })
    @DisplayName("应根据渠道返回正确的验证服务名称")
    void shouldReturnCorrectServiceName(String channel, String expectedServiceName) {
        String serviceName = Constant.BeanName.getValidateServiceName(channel);
        assertThat(serviceName).isEqualTo(expectedServiceName);
    }

    @ParameterizedTest
    @EnumSource(PaymentConstant.Status.class)
    @DisplayName("所有状态值都应该有对应的处理逻辑")
    void shouldHandleAllStatusValues(PaymentConstant.Status status) {
        // 测试逻辑
    }
}
```

## 7. Mock 静态方法示例

```java
@DisplayName("静态方法 Mock 示例")
class StaticMethodMockExamples extends BaseUnitTest {

    @Test
    @DisplayName("Mock DateTimeUtil.currentSeconds()")
    void shouldMockCurrentSeconds() {
        try (MockedStatic<DateTimeUtil> mockedStatic = mockStatic(DateTimeUtil.class)) {
            // 设置静态方法的返回值
            mockedStatic.when(DateTimeUtil::currentSeconds).thenReturn(1609459200);

            // 执行测试
            var result = service.doSomething();

            // 验证
            assertThat(result.getTimestamp()).isEqualTo(1609459200);
        }
    }

    @Test
    @DisplayName("Mock JsonUtil")
    void shouldMockJsonUtil() {
        try (MockedStatic<JsonUtil> mockedJson = mockStatic(JsonUtil.class)) {
            mockedJson.when(() -> JsonUtil.json(any())).thenReturn("{\"mocked\":true}");
            mockedJson.when(() -> JsonUtil.parse(anyString(), eq(SomeDto.class)))
                .thenReturn(new SomeDto());

            // 执行测试
        }
    }

    @Test
    @DisplayName("Mock ReactiveHttpClient")
    void shouldMockReactiveHttpClient() {
        try (MockedStatic<ApplicationContextHelper> mockedHelper = mockStatic(ApplicationContextHelper.class);
             MockedStatic<ReactiveHttpClient> mockedHttpClient = mockStatic(ReactiveHttpClient.class)) {

            // Mock ApplicationContextHelper.getBean() 用于获取 WebClient
            mockedHelper.when(() -> ApplicationContextHelper.getBean(any(Class.class)))
                    .thenReturn(mock(WebClient.class));

            // Mock ReactiveHttpClient.postBody() 静态方法
            mockedHttpClient.when(() -> ReactiveHttpClient.postBody(
                            anyString(),                    // String url
                            any(Object.class),              // Object body
                            any(java.util.Map.class),       // Map<String, String> headers
                            eq(String.class)))              // Class<T> responseType
                    .thenReturn(Mono.just("success"));

            // 执行测试
        }
    }
}
```

## 8. 测试数据工厂示例

```java
public class TestDataFactory {

    public static final Integer TEST_APP = 1203;

    public static PaymentGoogle createGooglePayment() {
        return createGooglePayment(builder -> {});
    }

    public static PaymentGoogle createGooglePayment(Consumer<PaymentGoogle> customizer) {
        PaymentGoogle payment = new PaymentGoogle();
        payment.setId(1);
        payment.setApp(TEST_APP);
        payment.setTransactionId("GPA." + UUID.randomUUID().toString().substring(0, 19));
        payment.setUserId("123456789");
        payment.setDeviceId("device-" + UUID.randomUUID().toString().substring(0, 8));
        payment.setProductId("com.example.product");
        payment.setUsdPrice("9.99");
        payment.setCurrency("USD");
        payment.setPrice("9.99");
        payment.setStatus(PaymentConstant.Status.VERIFIED);
        payment.setEnv(PaymentConstant.Env.PRODUCTION);
        payment.setFinished(PaymentConstant.Finished.NO);
        payment.setPaymentTime((int) (System.currentTimeMillis() / 1000));
        customizer.accept(payment);
        return payment;
    }

    public static ValidateDto createValidateDto(String channel) {
        ValidateDto dto = new ValidateDto();
        dto.setChannel(channel);
        dto.setUserId("123456789");
        dto.setDeviceId("device-123");
        dto.setBillingInfo(createBillingInfo());
        return dto;
    }

    public static BillingInfoDto createBillingInfo() {
        BillingInfoDto dto = new BillingInfoDto();
        dto.setReceipt("{\"orderId\":\"GPA.1234\",\"packageName\":\"com.example\",\"productId\":\"product\",\"purchaseToken\":\"token\"}");
        dto.setTransactionId("GPA.1234");
        dto.setProductId("com.example.product");
        dto.setCurrency("USD");
        dto.setPrice("9.99");
        dto.setUsdPrice("9.99");
        return dto;
    }

    public static AppInfo createAppInfo() {
        AppInfo appInfo = new AppInfo();
        appInfo.setAppId(TEST_APP);
        appInfo.setAppName("Test App");
        appInfo.setAppKey("test-app-key");
        return appInfo;
    }
}
```

## 9. 复杂场景示例

### 9.1 带 Context 的响应式流测试

```java
@Test
@DisplayName("当使用 Context 时,应正确传递数据")
void shouldPassContextCorrectly() {
    // Given
    PurchaseTokenData tokenData = new PurchaseTokenData();
    
    // When & Then
    StepVerifier.create(
        service.methodThatUsesContext()
            .contextWrite(ctx -> StoreUtil.set(ctx, "purchaseTokenData", tokenData))
            .contextWrite(ctx -> ctx.put(CONTEXT_STORE_KEY, Maps.newConcurrentMap()))
    )
    .assertNext(result -> {
        assertThat(result).isNotNull();
    })
    .verifyComplete();
}
```

### 9.2 TrackerUtil.sendTrack 特殊语义

```java
@Test
@DisplayName("当 Track 发送成功时,应正常完成")
void completesSuccessfully_whenTrackSendsSuccessfully() {
    // Given - 成功场景:返回 Mono.empty()
    when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
            .thenReturn(Mono.empty());

    // When & Then
    StepVerifier.create(service.refundSave(payment))
            .assertNext(result -> {
                assertThat(result).isNotNull();
            })
            .verifyComplete();
}

@Test
@DisplayName("当 Track 发送失败时,应抛出异常")
void throwsException_whenTrackSendFails() {
    // Given - 失败场景:返回有值的 Mono(错误信息)
    when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
            .thenReturn(Mono.just("error: connection timeout"));

    // When & Then
    StepVerifier.create(service.refundSave(payment))
            .expectErrorSatisfies(throwable -> {
                assertThat(throwable).isInstanceOf(RuntimeException.class);
                assertThat(throwable.getMessage()).contains("send track error");
            })
            .verify();
}
```

### 9.3 跳过测试示例

```java
@Test
@Disabled("需要人工检查:ReactiveHttpClient Mock 设置问题,已尝试 3 次修复")
@DisplayName("当 HTTP 回调失败时,应抛出异常并设置消息可见性")
void throwsException_whenHttpCallbackFails() {
    // TODO: 需要人工检查
    // 问题:ReactiveHttpClient.postBody 的 Mock 设置无法正确工作
    // 已尝试:
    // 1. 使用 MockedStatic 直接 Mock ReactiveHttpClient
    // 2. 使用 ApplicationContextHelper Mock WebClient
    // 3. 调整参数匹配器(anyString, any(Object.class), any(Map.class))
    // 预期:当 HTTP 调用失败时,应抛出 NeedChangeMessageVisibilityException
    // 需要检查:ReactiveHttpClient 的实际实现,可能需要集成测试覆盖

    // 测试代码...
}
```
